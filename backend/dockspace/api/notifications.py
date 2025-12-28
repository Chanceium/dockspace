"""
Notification preferences and user notifications API endpoints.
Handles notification preferences storage and retrieval, plus user-specific notifications.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from dockspace.core.models import MailAccount, AuditLog, AppSettings
from dockspace.api.decorators import json_login_required


# Default notification preferences
DEFAULT_PREFERENCES = {
	# System notifications
	'systemChanges': {'email': True, 'browser': True},
	'accountActivity': {'email': True, 'browser': True},

	# Management notifications (admin only)
	'accountCreated': {'email': True, 'browser': False},
	'accountDeleted': {'email': True, 'browser': False},
	'groupChanges': {'email': False, 'browser': False},
	'settingsChanged': {'email': True, 'browser': False},
	'oidcClientChanges': {'email': True, 'browser': False},

	# Security notifications
	'newDeviceLogin': {'email': True, 'browser': True},
	'passwordChanged': {'email': True, 'browser': True},
	'twoFactorChanged': {'email': True, 'browser': True},
	'suspiciousActivity': {'email': True, 'browser': True},
}


@json_login_required
@require_http_methods(["GET"])
def get_preferences(request):
	"""Get notification preferences for current user."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Get preferences from metadata field, or use defaults
	preferences = mail_account.metadata.get('notification_preferences', DEFAULT_PREFERENCES.copy())

	return JsonResponse({
		'success': True,
		'preferences': preferences
	})


@json_login_required
@require_http_methods(["POST"])
def update_preferences(request):
	"""Update notification preferences for current user."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		data = json.loads(request.body)
		preferences = data.get('preferences', {})

		# Validate preference structure
		for key, value in preferences.items():
			if not isinstance(value, dict) or 'email' not in value or 'browser' not in value:
				return JsonResponse({
					'success': False,
					'error': f'Invalid preference format for {key}'
				}, status=400)

		# Store in metadata
		if 'metadata' not in mail_account.__dict__ or mail_account.metadata is None:
			mail_account.metadata = {}

		mail_account.metadata['notification_preferences'] = preferences
		mail_account.save()

		return JsonResponse({
			'success': True,
			'message': 'Notification preferences updated successfully'
		})

	except json.JSONDecodeError:
		return JsonResponse({
			'success': False,
			'error': 'Invalid JSON'
		}, status=400)
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=500)


def _should_show_notification(action, is_admin, preferences):
	"""
	Determine if a notification should be shown based on action type and preferences.
	Returns (should_show_browser, should_send_email, category)
	"""
	# Map audit actions to notification preference keys
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

	pref_key = action_map.get(action)
	if not pref_key:
		return False, False, None

	# Admin-only notifications
	admin_only = pref_key in ['accountCreated', 'accountDeleted', 'groupChanges', 'settingsChanged', 'oidcClientChanges']
	if admin_only and not is_admin:
		return False, False, None

	pref = preferences.get(pref_key, {'email': False, 'browser': False})
	return pref.get('browser', False), pref.get('email', False), pref_key


@json_login_required
@require_http_methods(["GET"])
def get_notifications(request):
	"""
	Get recent notifications for current user based on audit logs and preferences.
	Personal notifications show actions affecting the user.
	Admin notifications show all management actions.
	"""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Get user preferences and dismissed notifications
	preferences = mail_account.metadata.get('notification_preferences', DEFAULT_PREFERENCES.copy())
	dismissed_notifications = mail_account.metadata.get('dismissed_notifications', [])

	# Get audit logs from last 7 days
	cutoff_date = timezone.now() - timedelta(days=7)

	# Build query based on user role
	if mail_account.is_admin:
		# Admins see: their own actions + actions affecting them + management events
		query = Q(created_at__gte=cutoff_date) & (
			Q(actor=mail_account) |  # Actions they performed
			Q(target_type='MailAccount', target_id=mail_account.id) |  # Actions affecting them
			Q(action__in=[  # Management events
				'account.create', 'account.delete',
				'group.create', 'group.update', 'group.delete',
				'settings.update', 'settings.smtp_update',
				'oidc.client_create', 'oidc.client_update', 'oidc.client_delete'
			])
		)
	else:
		# Regular users only see actions affecting them
		query = Q(created_at__gte=cutoff_date) & (
			Q(actor=mail_account) |  # Their own actions
			Q(target_type='MailAccount', target_id=mail_account.id)  # Actions affecting them
		)

	logs = AuditLog.objects.filter(query).select_related('actor').order_by('-created_at')[:50]

	# Filter and format notifications based on preferences
	notifications = []
	for log in logs:
		# Skip dismissed notifications
		if log.id in dismissed_notifications:
			continue

		should_show_browser, should_send_email, category = _should_show_notification(
			log.action,
			mail_account.is_admin,
			preferences
		)

		if not should_show_browser:
			continue

		# Determine if this is a personal or admin notification
		is_personal = (
			log.target_type == 'MailAccount' and
			log.target_id == mail_account.id
		)

		notifications.append({
			'id': log.id,
			'action': log.action,
			'action_display': log.get_action_display(),
			'description': log.description,
			'created_at': log.created_at.isoformat(),
			'severity': log.severity,
			'category': category,
			'is_personal': is_personal,
			'is_admin_only': category in ['accountCreated', 'accountDeleted', 'groupChanges', 'settingsChanged', 'oidcClientChanges'],
			'actor': {
				'id': log.actor.id,
				'name': f"{log.actor.first_name} {log.actor.last_name}".strip() or log.actor.email
			} if log.actor else None,
		})

	return JsonResponse({
		'success': True,
		'notifications': notifications,
		'unread_count': len(notifications)  # Could track read/unread in future
	})


@json_login_required
@require_http_methods(["GET"])
def get_unread_count(request):
	"""Get count of unread notifications."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Get user preferences and dismissed notifications
	preferences = mail_account.metadata.get('notification_preferences', DEFAULT_PREFERENCES.copy())
	dismissed_notifications = mail_account.metadata.get('dismissed_notifications', [])

	# Get audit logs from last 24 hours for unread count
	cutoff_date = timezone.now() - timedelta(hours=24)

	# Build query based on user role
	if mail_account.is_admin:
		query = Q(created_at__gte=cutoff_date) & (
			Q(actor=mail_account) |
			Q(target_type='MailAccount', target_id=mail_account.id) |
			Q(action__in=[
				'account.create', 'account.delete',
				'group.create', 'group.update', 'group.delete',
				'settings.update', 'settings.smtp_update',
				'oidc.client_create', 'oidc.client_update', 'oidc.client_delete'
			])
		)
	else:
		query = Q(created_at__gte=cutoff_date) & (
			Q(actor=mail_account) |
			Q(target_type='MailAccount', target_id=mail_account.id)
		)

	logs = AuditLog.objects.filter(query)

	# Count notifications that should be shown
	count = 0
	for log in logs:
		# Skip dismissed notifications
		if log.id in dismissed_notifications:
			continue

		should_show_browser, _, _ = _should_show_notification(
			log.action,
			mail_account.is_admin,
			preferences
		)
		if should_show_browser:
			count += 1

	return JsonResponse({
		'success': True,
		'count': count
	})


@json_login_required
@require_http_methods(["GET"])
def check_smtp_configured(request):
	"""Check if SMTP is configured for outbound email."""
	try:
		app_settings = AppSettings.load()
		# SMTP is configured if there's a host and from_email is not the default
		is_configured = bool(
			app_settings.smtp_host and
			app_settings.smtp_from_email and
			app_settings.smtp_from_email != 'noreply@example.com'
		)
		return JsonResponse({
			'success': True,
			'smtp_configured': is_configured
		})
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=500)


@json_login_required
@require_http_methods(["POST"])
def dismiss_notification(request, notification_id):
	"""Dismiss a notification for the current user."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		# Verify the notification exists
		notification = AuditLog.objects.get(id=notification_id)

		# Initialize metadata if needed
		if mail_account.metadata is None:
			mail_account.metadata = {}

		# Initialize dismissed_notifications list if needed
		if 'dismissed_notifications' not in mail_account.metadata:
			mail_account.metadata['dismissed_notifications'] = []

		# Add notification ID to dismissed list if not already there
		if notification_id not in mail_account.metadata['dismissed_notifications']:
			mail_account.metadata['dismissed_notifications'].append(notification_id)
			mail_account.save()

		return JsonResponse({
			'success': True,
			'message': 'Notification dismissed'
		})

	except AuditLog.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Notification not found'
		}, status=404)
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=500)
