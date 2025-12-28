"""
Module: integrations/hooks.py
Purpose: OIDC authorization hooks for access control

Provides hook functions for the OIDC provider to enforce access control rules:
- enforce_group_access: Restricts OIDC client access based on MailGroup membership and 2FA

Key Features:
- Group-based access control for OIDC clients
- Two-factor authentication (TOTP) enforcement
- Session-based TOTP verification tracking
- Automatic redirect to access denied or 2FA required pages
- Comprehensive logging for debugging authorization issues
"""
import logging
from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)


def _resolve_account(user):
    """Return MailAccount associated with user or via email lookup."""
    account = getattr(user, "account", None)
    if account:
        return account
    email = getattr(user, "email", "") or ""
    if not email:
        return None
    from dockspace.core.models import MailAccount

    try:
        account = MailAccount.objects.get(email__iexact=email)
        user.account = account
        return account
    except MailAccount.DoesNotExist:
        return None


def _session_totp_verified(request, account_id):
    """Check if the current session completed TOTP for the account."""
    try:
        return int(request.session.get("totp_verified_account")) == int(account_id)
    except (TypeError, ValueError):
        return False


def enforce_group_access(request, user, client, **kwargs):
    """
    OIDC hook that restricts client usage to MailAccount users and enforces optional group membership and 2FA.

    Rules:
    - Only authenticated users reach this hook (handled by oidc_provider).
    - If the client requires 2FA, users must have completed TOTP verification.
    - If the client has no group bindings, any user may proceed.
    - If the client has group bindings, the MailAccount must belong to at least one.
    """
    logger.info(f"enforce_group_access called for user={user}, client={client.client_id}")

    group_access = getattr(client, "group_access", None)
    logger.info(f"group_access for client {client.client_id}: {group_access}")

    account = _resolve_account(user)

    # Check if 2FA is required for this client
    if group_access and group_access.require_2fa:
        logger.info(f"Client {client.client_id} requires 2FA")
        is_verified = False
        if hasattr(user, "is_verified"):
            try:
                is_verified = user.is_verified()
            except TypeError:
                is_verified = bool(user.is_verified)
        if not is_verified and account:
            is_verified = _session_totp_verified(request, account.id) or bool(account.totp_verified_at)

        if not account or not account.totp_secret or not is_verified:
            logger.warning(f"User {user} failed 2FA verification for client requiring 2FA")
            client_name = client.name or client.client_id
            # Vue SPA route for 2FA required
            return HttpResponseRedirect(f"/two-factor-required?client={client_name}")

    if group_access is None:
        logger.info(f"No group restrictions for client {client.client_id}, allowing access")
        return None

    groups = group_access.groups.all()
    logger.info(f"Required groups for client {client.client_id}: {list(groups.values_list('name', flat=True))}")

    required_groups = list(groups.values_list("id", "name"))

    if not required_groups:
        logger.info(f"No specific groups required for client {client.client_id}, allowing access")
        return None

    if account is None:
        logger.warning(f"No account found for user {user}, denying access")
        request.session["access_denied_context"] = {
            "client_name": client.name or client.client_id,
            "required_groups": [name for _, name in required_groups],
            "user_groups": [],
        }
        # Vue SPA route for access denied
        return HttpResponseRedirect("/access-denied")

    user_groups = list(account.mail_groups.values_list("name", flat=True))
    logger.info(f"User {account.email} belongs to groups: {user_groups}")

    required_group_ids = [gid for gid, _ in required_groups]
    has_access = account.mail_groups.filter(id__in=required_group_ids).exists()

    if has_access:
        logger.info(f"User {account.email} has access to client {client.client_id}")
        return None

    logger.warning(f"User {account.email} does NOT belong to any required groups for client {client.client_id}")
    request.session["access_denied_context"] = {
        "client_name": client.name or client.client_id,
        "required_groups": [name for _, name in required_groups],
        "user_groups": user_groups,
    }
    # Vue SPA route for access denied
    return HttpResponseRedirect("/access-denied")
