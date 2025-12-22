import crypt
from typing import Optional

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.utils import timezone
from types import MethodType

from .models import MailAccount


class AccountUserBackend(BaseBackend):
    """Authenticate a MailAccount by email + password_hash, expose as an in-memory Django User surrogate.

    We return a lightweight Django User surrogate for session compatibility but do not persist it.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get("email") or "").strip()
        if not identifier or not password:
            return None

        account = None
        try:
            account = MailAccount.objects.get(username__iexact=identifier, is_active=True)
        except MailAccount.DoesNotExist:
            try:
                account = MailAccount.objects.get(email__iexact=identifier, is_active=True)
            except MailAccount.DoesNotExist:
                return None

        if not account.password_hash:
            return None

        if not self._verify_sha512(password, account.password_hash):
            return None

        # Get or create a Django User record to satisfy OIDC provider foreign keys
        if account.user:
            user = account.user
            # Update user fields if they changed
            user.username = account.email
            user.email = account.email
            user.is_active = account.is_active
            user.last_login = timezone.now()
            user.save()
        else:
            user = User.objects.create(
                username=account.email,
                email=account.email,
                is_staff=False,
                is_superuser=False,
                is_active=account.is_active,
                last_login=timezone.now(),
            )
            # Link the user to the account
            account.user = user
            account.save()

        # Attach the account for later access.
        user.account = account
        return user

    def get_user(self, user_id):
        try:
            account = MailAccount.objects.get(pk=user_id)
        except MailAccount.DoesNotExist:
            return None

        # Get or create the User record if not already linked
        if account.user:
            user = account.user
        else:
            user = User.objects.create(
                username=account.email,
                email=account.email,
                is_staff=False,
                is_superuser=False,
                is_active=account.is_active,
            )
            # Link the user to the account
            account.user = user
            account.save()

        user.account = account
        return user

    def _verify_sha512(self, raw_password: str, stored_hash: str) -> bool:
        # stored_hash expected like {SHA512-CRYPT}$6$salt$rest
        if not stored_hash:
            return False
        if stored_hash.startswith("{SHA512-CRYPT}"):
            stored_hash = stored_hash[len("{SHA512-CRYPT}") :]
        candidate = crypt.crypt(raw_password, stored_hash)
        return candidate == stored_hash


class AccountUserWithTOTPBackend(AccountUserBackend):
    """Authenticate MailAccount with optional TOTP secret; if present, require otp_token param."""

    def authenticate(self, request, username=None, password=None, otp_token=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if not user:
            return None
        account = getattr(user, "account", None)
        if account and account.totp_secret:
            token = otp_token or kwargs.get("otp_token") or (request.POST.get("otp_token") if request else None)
            if not token:
                return None
            if not self._verify_totp(account, token):
                return None
        return user

    def _verify_totp(self, account: MailAccount, token: str) -> bool:
        try:
            import pyotp

            totp = pyotp.TOTP(account.totp_secret)
            ok = totp.verify(token, valid_window=1)
            if ok:
                MailAccount.objects.filter(pk=account.pk).update(
                    totp_last_counter=account.totp_last_counter + 1,
                    totp_verified_at=timezone.now(),
                )
            return ok
        except Exception:
            return False
