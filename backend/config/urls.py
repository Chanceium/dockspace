"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from two_factor import urls as tf_urls
from dockspace.core import views as dock_views

# Import API views from organized modules
from dockspace.api import auth, settings as api_settings, profile, totp, mail, mail_client, oidc, sessions, audit, notifications

urlpatterns = [
    # ========================================================================
    # Authentication API
    # ========================================================================
    path('api/csrf/', auth.get_csrf_token, name='api_csrf'),
    path('api/auth/login/', auth.login_view, name='api_login'),
    path('api/auth/logout/', auth.logout_view, name='api_logout'),
    path('api/auth/session/', auth.session_check, name='api_session'),
    path('api/auth/register/', auth.register, name='api_register'),
    path('api/setup/check/', auth.setup_check, name='api_setup_check'),
    path('api/setup/complete/', auth.setup_complete, name='api_setup_complete'),

    # ========================================================================
    # App Settings API
    # ========================================================================
    path('api/settings/', api_settings.get_settings, name='api_settings_get'),
    path('api/settings/update/', api_settings.update_settings, name='api_settings_update'),

    # ========================================================================
    # Profile API
    # ========================================================================
    path('api/profile/', profile.get_profile, name='api_profile_get'),
    path('api/profile/update/', profile.update_profile, name='api_profile_update'),
    path('api/profile/upload-photo/', profile.upload_profile_photo, name='api_profile_upload_photo'),
    path('api/profile/password-requirements/', profile.get_password_requirements, name='api_password_requirements'),
    path('api/profile/deactivate/', profile.deactivate_account, name='api_profile_deactivate'),
    path('api/profile/change-password/', profile.change_password, name='api_change_password'),

    # ========================================================================
    # TOTP / Two-Factor Authentication API
    # ========================================================================
    path('api/totp/status/', totp.get_totp_status, name='api_totp_status'),
    path('api/totp/devices/', totp.list_devices, name='api_totp_list_devices'),
    path('api/totp/devices/create/', totp.create_device, name='api_totp_create_device'),
    path('api/totp/devices/verify/', totp.verify_device, name='api_totp_verify_device'),
    path('api/totp/devices/<int:device_id>/delete/', totp.delete_device, name='api_totp_delete_device'),
    # Legacy endpoints
    path('api/totp/generate/', totp.generate_totp, name='api_totp_generate'),
    path('api/totp/verify/', totp.verify_totp, name='api_totp_verify'),
    path('api/totp/disable/', totp.disable_totp, name='api_totp_disable'),

    # ========================================================================
    # User Sessions API
    # ========================================================================
    path('api/sessions/', sessions.list_sessions, name='api_sessions_list'),

    # ========================================================================
    # Mail Client API (IMAP/SMTP user mailboxes)
    # ========================================================================
    path('api/mailboxes/', mail_client.list_mailboxes, name='api_mailboxes_list'),
    path('api/mailboxes/create/', mail_client.create_mailbox, name='api_mailbox_create'),
    path('api/mailboxes/<int:mailbox_id>/update/', mail_client.update_mailbox, name='api_mailbox_update'),
    path('api/mailboxes/<int:mailbox_id>/delete/', mail_client.delete_mailbox, name='api_mailbox_delete'),
    path('api/mailboxes/<int:mailbox_id>/test/', mail_client.test_mailbox_connection, name='api_mailbox_test'),
    path('api/mailboxes/<int:mailbox_id>/folders/', mail_client.list_folders, name='api_mailbox_folders'),
    path('api/mailboxes/<int:mailbox_id>/emails/', mail_client.fetch_emails, name='api_mailbox_emails'),
    path('api/mailboxes/<int:mailbox_id>/emails/<str:email_id>/', mail_client.fetch_email_detail, name='api_mailbox_email_detail'),
    path('api/mailboxes/<int:mailbox_id>/send/', mail_client.send_email, name='api_mailbox_send'),

    # ========================================================================
    # Mail Accounts API (Postfix/Dovecot account management)
    # ========================================================================
    path('api/mail/accounts/', mail.list_accounts, name='api_account_list'),
    path('api/mail/accounts/create/', mail.create_account, name='api_account_create'),
    path('api/mail/accounts/<int:account_id>/update/', mail.update_account, name='api_account_update'),
    path('api/mail/accounts/<int:account_id>/delete/', mail.delete_account, name='api_account_delete'),

    # ========================================================================
    # Mail Quotas API
    # ========================================================================
    path('api/mail/quotas/', mail.list_quotas, name='api_quota_list'),
    path('api/mail/quotas/<int:account_id>/', mail.get_quota, name='api_quota_get'),
    path('api/mail/quotas/create/', mail.create_quota, name='api_quota_create'),
    path('api/mail/quotas/<int:quota_id>/delete/', mail.delete_quota, name='api_quota_delete'),

    # ========================================================================
    # Mail Aliases API
    # ========================================================================
    path('api/mail/aliases/', mail.list_aliases, name='api_alias_list'),
    path('api/mail/aliases/create/', mail.create_alias, name='api_alias_create'),
    path('api/mail/aliases/<int:alias_id>/delete/', mail.delete_alias, name='api_alias_delete'),

    # ========================================================================
    # Mail Groups API
    # ========================================================================
    path('api/mail/groups/', mail.list_groups, name='api_group_list'),
    path('api/mail/groups/<int:group_id>/', mail.get_group, name='api_group_get'),
    path('api/mail/groups/create/', mail.create_group, name='api_group_create'),
    path('api/mail/groups/<int:group_id>/update/', mail.update_group, name='api_group_update'),
    path('api/mail/groups/<int:group_id>/delete/', mail.delete_group, name='api_group_delete'),

    # ========================================================================
    # Account Groups API (assign groups to accounts)
    # ========================================================================
    path('api/mail/accounts/<int:account_id>/groups/', mail.get_account_groups, name='api_account_groups_get'),
    path('api/mail/accounts/<int:account_id>/groups/update/', mail.update_account_groups, name='api_account_groups_update'),
    path('api/mail/accounts/<int:account_id>/password/reset/', mail.reset_account_password, name='api_account_password_reset'),

    # ========================================================================
    # OIDC Clients API
    # ========================================================================
    path('api/oidc/clients/', oidc.list_clients, name='api_client_list'),
    path('api/oidc/clients/<int:client_id>/', oidc.get_client, name='api_client_get'),
    path('api/oidc/clients/create/', oidc.create_client, name='api_client_create'),
    path('api/oidc/clients/<int:client_id>/update/', oidc.update_client, name='api_client_update'),
    path('api/oidc/clients/<int:client_id>/delete/', oidc.delete_client, name='api_client_delete'),

    # ========================================================================
    # Client Access Control API
    # ========================================================================
    path('api/oidc/clients/<int:client_id>/access/', oidc.get_client_access, name='api_client_access_get'),
    path('api/oidc/clients/<int:client_id>/access/update/', oidc.update_client_access, name='api_client_access_update'),

    # ========================================================================
    # Audit Logs API
    # ========================================================================
    path('api/audit/logs/', audit.list_audit_logs, name='api_audit_list'),
    path('api/audit/stats/', audit.get_audit_stats, name='api_audit_stats'),

    # ========================================================================
    # Notifications API
    # ========================================================================
    path('api/notifications/preferences/', notifications.get_preferences, name='api_notifications_get_preferences'),
    path('api/notifications/preferences/update/', notifications.update_preferences, name='api_notifications_update_preferences'),
    path('api/notifications/', notifications.get_notifications, name='api_notifications_list'),
    path('api/notifications/unread-count/', notifications.get_unread_count, name='api_notifications_unread_count'),
    path('api/notifications/smtp-status/', notifications.check_smtp_configured, name='api_notifications_smtp_status'),
    path('api/notifications/<int:notification_id>/dismiss/', notifications.dismiss_notification, name='api_notifications_dismiss'),

    # ========================================================================
    # Two-factor auth URLs
    # ========================================================================
    path('', include((tf_urls.urlpatterns[0], 'two_factor'), namespace='two_factor')),

    # ========================================================================
    # OIDC provider URLs (for OAuth/OpenID Connect)
    # ========================================================================
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
]

# Django Admin panel - only enabled if ENABLE_DJANGO_ADMIN=true
if os.getenv('ENABLE_DJANGO_ADMIN', 'false').lower() == 'true':
    urlpatterns.append(path('admin/', admin.site.urls))

# Protected media files (authentication required)
urlpatterns.append(re_path(r'^media/(?P<path>.*)$', dock_views.protected_media, name='protected_media'))

# Static files are served by WhiteNoise middleware (configured in settings.py)
# In development, Django's staticfiles app handles this
# In production, collectstatic + WhiteNoise handles this

# Catch-all: Serve Vue.js SPA for all other routes (Vue Router handles client-side routing)
# Important: This must be LAST so static files are served first
# Static files are at /static/* and are handled by staticfiles/WhiteNoise
urlpatterns.append(re_path(r'^(?!static/).*$', dock_views.vue_spa_view, name='vue_spa'))

# Custom handler for non-matched URLs (used when DEBUG=False)
handler404 = 'dockspace.core.views.vue_spa_view'
