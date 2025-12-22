from django.http import HttpResponseForbidden


def enforce_group_access(request, user, client, **kwargs):
    """
    OIDC hook that restricts client usage to MailAccount users, enforces 2FA, and optional group membership.

    Rules:
    - Only authenticated users reach this hook (handled by oidc_provider).
    - Users must have completed OTP verification (django-otp).
    - If the client has no group bindings, any user may proceed.
    - If the client has group bindings, the MailAccount must belong to at least one.
    """
    # For AccountUser proxies, we don't have django-otp; rely on otp_token enforcement upstream.
    if hasattr(user, "is_verified"):
        is_verified = False
        try:
            is_verified = user.is_verified()
        except TypeError:
            is_verified = bool(user.is_verified)
        if not is_verified:
            return HttpResponseForbidden("Two-factor authentication required.")

    group_access = getattr(client, "group_access", None)
    if group_access is None:
        return None

    groups = group_access.groups.all()
    if not groups.exists():
        return None

    account = getattr(user, "account", None)
    if account is None:
        # Try to resolve MailAccount by email as a fallback (e.g., staff user)
        from dockspace.models import MailAccount

        try:
            account = MailAccount.objects.get(email__iexact=getattr(user, "email", ""))
        except MailAccount.DoesNotExist:
            account = None

    if account is None:
        return HttpResponseForbidden("You do not have access to this client.")

    if account.mail_groups.filter(id__in=groups.values_list("id", flat=True)).exists():
        return None

    return HttpResponseForbidden("You do not have access to this client.")
