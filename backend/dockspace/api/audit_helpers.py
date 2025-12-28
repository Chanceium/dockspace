"""
Module: audit_helpers.py
Purpose: Helper functions for consistent audit logging across API endpoints

This module provides utility functions to make audit logging easier and more
consistent throughout the application. It handles extracting request context,
building audit log entries, and common patterns.

Key Functions:
- get_request_context(): Extract actor, IP, and user agent from request
- log_action(): Simplified wrapper around AuditLog.log()
- audit_decorator(): Decorator to automatically log API actions

Author: System
Created: 2024-12-27
"""

import threading
from functools import wraps
from django.core.mail import send_mail
from django.conf import settings
from dockspace.core.models import AuditLog, AppSettings, MailAccount


def get_client_ip(request):
    """
    Return the client IP, honoring X-Forwarded-For when behind a proxy.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # left-most entry is the original client
        parts = [ip.strip() for ip in xff.split(',') if ip.strip()]
        if parts:
            return parts[0]
    return request.META.get('REMOTE_ADDR')


def get_request_context(request):
    """
    Extract audit logging context from Django request.

    Args:
        request: Django HttpRequest object

    Returns:
        dict: Contains actor, ip_address, and user_agent
    """
    return {
        'actor': getattr(request.user, 'account', None) if request.user.is_authenticated else None,
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }


def log_action(action, request, target_type=None, target_id=None, target_name=None,
               description='', metadata=None, severity='info', success=True):
    """
    Log an audit action with request context automatically extracted.

    Args:
        action: Action type (e.g., 'account.create')
        request: Django HttpRequest object
        target_type: Type of object affected (e.g., 'MailAccount')
        target_id: ID of affected object
        target_name: Human-readable name of affected object
        description: Human-readable description
        metadata: Additional structured data
        severity: 'info', 'warning', or 'critical'
        success: Whether action succeeded

    Returns:
        AuditLog: The created audit log entry
    """
    context = get_request_context(request)

    audit_log = AuditLog.log(
        action=action,
        actor=context['actor'],
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        description=description,
        metadata=metadata or {},
        ip_address=context['ip_address'],
        user_agent=context['user_agent'],
        severity=severity,
        success=success,
    )

    # Send email notifications if configured
    send_notification_email(audit_log)

    return audit_log


def audit_login_attempt(request, email, success, reason=''):
    """
    Log a login attempt (successful or failed).

    Args:
        request: Django HttpRequest object
        email: Email address used for login
        success: Whether login succeeded
        reason: Reason for failure (if applicable)
    """
    context = get_request_context(request)

    # Try to get target_id for the account
    target_id = None
    if success and context['actor']:
        target_id = context['actor'].id
    else:
        # For failed logins, try to find the account
        try:
            account = MailAccount.objects.get(email=email)
            target_id = account.id
        except MailAccount.DoesNotExist:
            pass

    audit_log = AuditLog.log(
        action='auth.login' if success else 'auth.login_failed',
        actor=context['actor'] if success else None,
        target_type='MailAccount',
        target_id=target_id,
        target_name=email,
        description=f"Login {'successful' if success else 'failed'} for {email}" + (f": {reason}" if reason else ""),
        metadata={'email': email, 'reason': reason} if reason else {'email': email},
        ip_address=context['ip_address'],
        user_agent=context['user_agent'],
        severity='info' if success else 'warning',
        success=success,
    )

    # Send email notifications if configured
    send_notification_email(audit_log)

    return audit_log


def audit_logout(request):
    """Log a logout action."""
    context = get_request_context(request)
    actor = context['actor']

    audit_log = AuditLog.log(
        action='auth.logout',
        actor=actor,
        target_type='MailAccount',
        target_id=getattr(actor, 'id', None),
        target_name=getattr(actor, 'email', None),
        description=f"User logged out: {actor.email if actor else 'Unknown'}",
        ip_address=context['ip_address'],
        user_agent=context['user_agent'],
        severity='info',
        success=True,
    )

    # Send email notifications if configured
    send_notification_email(audit_log)

    return audit_log


def audit_password_change(request, account, changed_by_admin=False):
    """
    Log a password change.

    Args:
        request: Django HttpRequest object
        account: MailAccount whose password was changed
        changed_by_admin: Whether an admin changed another user's password
    """
    context = get_request_context(request)

    description = f"Password changed for {account.email}"
    if changed_by_admin and context['actor']:
        description = f"Admin {context['actor'].email} changed password for {account.email}"

    audit_log = AuditLog.log(
        action='account.password_change',
        actor=context['actor'],
        target_type='MailAccount',
        target_id=account.id,
        target_name=account.email,
        description=description,
        metadata={'changed_by_admin': changed_by_admin},
        ip_address=context['ip_address'],
        user_agent=context['user_agent'],
        severity='warning' if changed_by_admin else 'info',
        success=True,
    )

    # Send email notifications if configured
    send_notification_email(audit_log)

    return audit_log


def audit_2fa_change(request, account, enabled):
    """
    Log 2FA being enabled or disabled.

    Args:
        request: Django HttpRequest object
        account: MailAccount whose 2FA was changed
        enabled: Whether 2FA was enabled (True) or disabled (False)
    """
    context = get_request_context(request)

    audit_log = AuditLog.log(
        action='auth.2fa_enabled' if enabled else 'auth.2fa_disabled',
        actor=context['actor'],
        target_type='MailAccount',
        target_id=account.id,
        target_name=account.email,
        description=f"2FA {'enabled' if enabled else 'disabled'} for {account.email}",
        ip_address=context['ip_address'],
        user_agent=context['user_agent'],
        severity='info',
        success=True,
    )

    # Send email notifications if configured
    send_notification_email(audit_log)

    return audit_log


def audit_account_status_change(request, account, new_status, old_status):
    """
    Log account activation/suspension.

    Args:
        request: Django HttpRequest object
        account: MailAccount whose status changed
        new_status: New status value
        old_status: Previous status value
    """
    context = get_request_context(request)

    action = 'account.suspend' if new_status.lower() == 'suspended' else 'account.activate'
    severity = 'warning' if new_status.lower() == 'suspended' else 'info'

    audit_log = AuditLog.log(
        action=action,
        actor=context['actor'],
        target_type='MailAccount',
        target_id=account.id,
        target_name=account.email,
        description=f"Account status changed from {old_status} to {new_status} for {account.email}",
        metadata={'old_status': old_status, 'new_status': new_status},
        ip_address=context['ip_address'],
        user_agent=context['user_agent'],
        severity=severity,
        success=True,
    )

    # Send email notifications if configured
    send_notification_email(audit_log)

    return audit_log


def is_smtp_configured():
    """
    Check if SMTP is properly configured for sending emails.

    Returns:
        bool: True if SMTP is configured, False otherwise
    """
    try:
        app_settings = AppSettings.load()
        # SMTP is configured if there's a host and from_email is not the default
        return bool(
            app_settings.smtp_host and
            app_settings.smtp_from_email and
            app_settings.smtp_from_email != 'noreply@example.com'
        )
    except Exception:
        return False


def get_notification_category(action):
    """
    Map audit action to notification category.

    Args:
        action: Audit action string (e.g., 'account.create')

    Returns:
        str or None: Notification category key
    """
    action_map = {
        # System notifications
        'settings.update': 'systemChanges',
        'settings.smtp_update': 'systemChanges',
        'account.profile_update': 'accountActivity',

        # Management notifications (admin only)
        'account.create': 'accountCreated',
        'account.delete': 'accountDeleted',
        'group.create': 'groupChanges',
        'group.update': 'groupChanges',
        'group.delete': 'groupChanges',
        'group.members_update': 'groupChanges',
        'oidc.client_create': 'oidcClientChanges',
        'oidc.client_update': 'oidcClientChanges',
        'oidc.client_delete': 'oidcClientChanges',
        'oidc.access_update': 'oidcClientChanges',

        # Security notifications
        'auth.login': 'newDeviceLogin',
        'auth.login_failed': 'suspiciousActivity',
        'account.password_change': 'passwordChanged',
        'auth.2fa_enabled': 'twoFactorChanged',
        'auth.2fa_disabled': 'twoFactorChanged',
        'account.suspend': 'suspiciousActivity',
        'account.activate': 'accountActivity',
    }
    return action_map.get(action)


def _send_email_async(subject, message, from_email, recipient_email):
    """
    Internal function to send email in background thread.

    Args:
        subject: Email subject
        message: Email body
        from_email: From email address
        recipient_email: Recipient email address
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=True,  # Don't raise exceptions if email fails
        )
    except Exception as e:
        # Log error but don't interrupt anything
        print(f"Failed to send notification email to {recipient_email}: {e}")


def send_notification_email(audit_log):
    """
    Send email notifications based on audit log and user preferences.
    Emails are sent asynchronously to avoid blocking the request.

    Args:
        audit_log: AuditLog instance
    """
    if not is_smtp_configured():
        return

    category = get_notification_category(audit_log.action)
    if not category:
        return

    # Determine which users should receive this notification
    recipients = []

    # Admin-only categories
    admin_only_categories = ['accountCreated', 'accountDeleted', 'groupChanges', 'settingsChanged', 'oidcClientChanges']
    is_admin_only = category in admin_only_categories

    if is_admin_only:
        # Send to all admins who have this preference enabled
        admin_accounts = MailAccount.objects.filter(is_admin=True)
        for admin in admin_accounts:
            preferences = admin.metadata.get('notification_preferences', {})
            pref = preferences.get(category, {})
            if pref.get('email', False):
                recipients.append(admin)
    else:
        # Personal notification - send to the affected user if they have preference enabled
        if audit_log.target_type == 'MailAccount' and audit_log.target_id:
            try:
                target_account = MailAccount.objects.get(id=audit_log.target_id)
                preferences = target_account.metadata.get('notification_preferences', {})
                pref = preferences.get(category, {})
                if pref.get('email', False):
                    recipients.append(target_account)
            except MailAccount.DoesNotExist:
                pass

    # Send emails asynchronously in background threads
    if recipients:
        app_settings = AppSettings.load()
        subject = f"[Dockspace] {audit_log.get_action_display()}"

        for recipient in recipients:
            message = f"""
{audit_log.description}

Action: {audit_log.get_action_display()}
Severity: {audit_log.get_severity_display()}
Time: {audit_log.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
            if audit_log.actor:
                actor_name = f"{audit_log.actor.first_name} {audit_log.actor.last_name}".strip() or audit_log.actor.email
                message += f"Performed by: {actor_name}\n"

            message += f"\nThis is an automated notification from Dockspace."

            # Send email in background thread to avoid blocking request
            thread = threading.Thread(
                target=_send_email_async,
                args=(subject, message, app_settings.smtp_from_email, recipient.email),
                daemon=True  # Daemon thread won't prevent application shutdown
            )
            thread.start()
