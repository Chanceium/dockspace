import logging
from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)


def enforce_group_access(request, user, client, **kwargs):
    """
    OIDC hook that restricts client usage to MailAccount users, enforces 2FA, and optional group membership.

    Rules:
    - Only authenticated users reach this hook (handled by oidc_provider).
    - Users must have completed OTP verification (django-otp).
    - If the client has no group bindings, any user may proceed.
    - If the client has group bindings, the MailAccount must belong to at least one.
    """
    logger.info(f"enforce_group_access called for user={user}, client={client.client_id}")

    # For AccountUser proxies, we don't have django-otp; rely on otp_token enforcement upstream.
    if hasattr(user, "is_verified"):
        is_verified = False
        try:
            is_verified = user.is_verified()
        except TypeError:
            is_verified = bool(user.is_verified)
        if not is_verified:
            logger.warning(f"User {user} failed 2FA verification")
            return HttpResponseForbidden("Two-factor authentication required.")

    group_access = getattr(client, "group_access", None)
    logger.info(f"group_access for client {client.client_id}: {group_access}")

    if group_access is None:
        logger.info(f"No group restrictions for client {client.client_id}, allowing access")
        return None

    groups = group_access.groups.all()
    logger.info(f"Required groups for client {client.client_id}: {list(groups.values_list('name', flat=True))}")

    if not groups.exists():
        logger.info(f"No specific groups required for client {client.client_id}, allowing access")
        return None

    account = getattr(user, "account", None)
    if account is None:
        # Try to resolve MailAccount by email as a fallback (e.g., staff user)
        from dockspace.models import MailAccount

        try:
            account = MailAccount.objects.get(email__iexact=getattr(user, "email", ""))
            logger.info(f"Found account via email lookup: {account}")
        except MailAccount.DoesNotExist:
            account = None

    if account is None:
        logger.warning(f"No account found for user {user}, denying access")
        return HttpResponseForbidden("You do not have access to this client.")

    user_groups = list(account.mail_groups.values_list('name', flat=True))
    logger.info(f"User {account.email} belongs to groups: {user_groups}")

    required_group_ids = list(groups.values_list("id", flat=True))
    has_access = account.mail_groups.filter(id__in=required_group_ids).exists()

    if has_access:
        logger.info(f"User {account.email} has access to client {client.client_id}")
        return None

    logger.warning(f"User {account.email} does NOT belong to any required groups for client {client.client_id}")
    return HttpResponseForbidden("You do not have access to this client.")
