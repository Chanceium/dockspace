"""
Application settings API endpoints.
Handles global app configuration (admin only).
"""
import json
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dockspace.core.models import AppSettings
from dockspace.api.decorators import json_admin_required
from dockspace.api.audit_helpers import log_action


@json_admin_required
@require_http_methods(["GET"])
def get_settings(request):
	"""
	Get current app settings.
	Only accessible to admin users.
	"""
	app_settings = AppSettings.load()

	# Determine smtp_security from booleans
	if app_settings.smtp_use_ssl:
		smtp_security = 'ssl'
	elif app_settings.smtp_use_tls:
		smtp_security = 'starttls'
	else:
		smtp_security = 'none'

	return JsonResponse({
		'success': True,
		'settings': {
			'session_timeout': app_settings.session_timeout,
			'domain_url': app_settings.domain_url,
			'allow_registration': app_settings.allow_registration,
			'smtp_host': app_settings.smtp_host,
			'smtp_port': app_settings.smtp_port,
			'smtp_username': app_settings.smtp_username,
			'smtp_from_email': app_settings.smtp_from_email,
			'smtp_security': smtp_security,
		}
	})


@json_admin_required
@require_http_methods(["POST"])
def update_settings(request):
	"""
	Update app settings.
	Only accessible to admin users.
	"""
	try:
		data = json.loads(request.body)
		app_settings = AppSettings.load()

		# Track changes for audit log
		changed_fields = {}

		# Update fields
		session_timeout = data.get('session_timeout')
		if session_timeout is not None:
			if session_timeout < 300:
				return JsonResponse({
					'success': False,
					'error': 'Session timeout must be at least 5 minutes (300 seconds)'
				}, status=400)
			if app_settings.session_timeout != session_timeout:
				changed_fields['session_timeout'] = {'old': app_settings.session_timeout, 'new': session_timeout}
			app_settings.session_timeout = session_timeout

		domain_url = data.get('domain_url')
		if domain_url is not None:
			domain_url_stripped = domain_url.rstrip('/')
			if app_settings.domain_url != domain_url_stripped:
				changed_fields['domain_url'] = {'old': app_settings.domain_url, 'new': domain_url_stripped}
			app_settings.domain_url = domain_url_stripped

		if 'allow_registration' in data:
			new_value = bool(data.get('allow_registration'))
			if app_settings.allow_registration != new_value:
				changed_fields['allow_registration'] = {'old': app_settings.allow_registration, 'new': new_value}
			app_settings.allow_registration = new_value

		# Track SMTP changes
		smtp_changed = False

		if 'smtp_host' in data:
			if app_settings.smtp_host != data['smtp_host']:
				changed_fields['smtp_host'] = {'old': app_settings.smtp_host, 'new': data['smtp_host']}
				smtp_changed = True
			app_settings.smtp_host = data['smtp_host']
		if 'smtp_port' in data:
			if app_settings.smtp_port != data['smtp_port']:
				changed_fields['smtp_port'] = {'old': app_settings.smtp_port, 'new': data['smtp_port']}
				smtp_changed = True
			app_settings.smtp_port = data['smtp_port']
		if 'smtp_username' in data:
			if app_settings.smtp_username != data['smtp_username']:
				changed_fields['smtp_username'] = {'old': app_settings.smtp_username, 'new': data['smtp_username']}
				smtp_changed = True
			app_settings.smtp_username = data['smtp_username']
		if 'smtp_from_email' in data:
			if app_settings.smtp_from_email != data['smtp_from_email']:
				changed_fields['smtp_from_email'] = {'old': app_settings.smtp_from_email, 'new': data['smtp_from_email']}
				smtp_changed = True
			app_settings.smtp_from_email = data['smtp_from_email']

		# Handle password - only update if provided
		smtp_password = data.get('smtp_password')
		if smtp_password:
			changed_fields['smtp_password'] = '***'
			smtp_changed = True
			app_settings.smtp_password = smtp_password

		# Handle smtp_security choice
		smtp_security = data.get('smtp_security')
		if smtp_security is not None:
			old_security = 'ssl' if app_settings.smtp_use_ssl else ('starttls' if app_settings.smtp_use_tls else 'none')
			if old_security != smtp_security:
				changed_fields['smtp_security'] = {'old': old_security, 'new': smtp_security}
				smtp_changed = True
			app_settings.smtp_use_tls = smtp_security == 'starttls'
			app_settings.smtp_use_ssl = smtp_security == 'ssl'

		# Validate
		try:
			app_settings.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		app_settings.save()

		# Log settings update
		if changed_fields:
			log_action(
				action='settings.smtp_update' if smtp_changed else 'settings.update',
				request=request,
				target_type='AppSettings',
				target_id=1,
				target_name='Application Settings',
				description=f'{"SMTP settings" if smtp_changed else "Application settings"} updated',
				metadata={'changed_fields': changed_fields},
				severity='info',
				success=True
			)

		return JsonResponse({
			'success': True,
			'message': 'Settings updated successfully'
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
