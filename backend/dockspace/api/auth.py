"""
Authentication API endpoints.
Handles login, logout, registration, session management, and setup.
"""
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token

from dockspace.core.models import MailAccount, AppSettings
from dockspace.core.session_tracker import create_or_update_session, mark_session_inactive
from dockspace.api.audit_helpers import audit_login_attempt, audit_logout, log_action


@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
	"""
	Provide CSRF token for the frontend.
	This should be called on app initialization.
	"""
	return JsonResponse({
		'csrfToken': get_token(request)
	})


@require_http_methods(["POST"])
def login_view(request):
	"""
	Login endpoint for Vue3 frontend.
	Expects JSON body with email and password.
	Returns session-based authentication.
	"""
	try:
		data = json.loads(request.body)
		email = data.get('email', '').strip().lower()
		password = data.get('password', '')
		otp_token = data.get('otp_token', '')

		if not email or not password:
			return JsonResponse({
				'success': False,
				'error': 'Email and password are required'
			}, status=400)

		# Check if account exists but is suspended/deactivated before authentication
		try:
			mail_account = MailAccount.objects.get(email__iexact=email)
			account_status = getattr(mail_account, 'status', 'active')
			if account_status == 'suspended':
				audit_login_attempt(request, email, False, 'Account suspended')
				return JsonResponse({
					'success': False,
					'error': 'Your account has been suspended. Please contact an administrator.'
				}, status=403)
			elif account_status == 'deactivated':
				audit_login_attempt(request, email, False, 'Account deactivated')
				return JsonResponse({
					'success': False,
					'error': 'Your account has been deactivated. Please contact an administrator.'
				}, status=403)
		except MailAccount.DoesNotExist:
			pass

		# Authenticate using custom backend (AccountUserWithTOTPBackend)
		user = authenticate(request, username=email, password=password, otp_token=otp_token)

		if user is not None:
			# Check if account has TOTP but no token was provided
			account = getattr(user, 'account', None)

			# Check for TOTP requirement using new TOTPDevice model
			from dockspace.core.models import TOTPDevice
			verified_devices = TOTPDevice.objects.filter(
				account=account,
				verified_at__isnull=False
			).count()

			if verified_devices > 0 and not otp_token:
				# Don't log as failed - credentials were correct, just needs 2FA
				return JsonResponse({
					'success': False,
					'requiresTOTP': True,
					'error': 'Two-factor authentication required'
				}, status=401)

			login(request, user)

			# Log successful login
			audit_login_attempt(request, email, True)

			# Track this login session
			try:
				create_or_update_session(request, account)
			except Exception as e:
				# Don't fail login if session tracking fails
				import logging
				logger = logging.getLogger(__name__)
				logger.error(f"Failed to track session: {e}")

			# Get user data from the attached account
			user_data = {
				'id': account.id,
				'email': account.email,
				'username': account.username,
				'first_name': account.first_name,
				'last_name': account.last_name,
				'is_admin': account.is_admin,
				'picture': account.picture.url if account.picture else None,
			}

			return JsonResponse({
				'success': True,
				'user': user_data,
				'message': 'Login successful'
			})
		else:
			audit_login_attempt(request, email, False, 'Invalid credentials')
			return JsonResponse({
				'success': False,
				'error': 'Invalid credentials'
			}, status=401)

	except json.JSONDecodeError:
		return JsonResponse({
			'success': False,
			'error': 'Invalid JSON'
		}, status=400)
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': 'An error occurred during login'
		}, status=500)


@require_http_methods(["POST"])
def logout_view(request):
	"""Logout endpoint for Vue3 frontend."""
	# Log logout before clearing session
	if request.user.is_authenticated:
		audit_logout(request)

	# Mark session as inactive before logging out
	try:
		session_key = request.session.session_key
		if session_key:
			mark_session_inactive(session_key)
	except Exception as e:
		# Don't fail logout if session tracking fails
		import logging
		logger = logging.getLogger(__name__)
		logger.error(f"Failed to mark session inactive: {e}")

	logout(request)
	return JsonResponse({
		'success': True,
		'message': 'Logged out successfully'
	})


@require_http_methods(["GET"])
def session_check(request):
	"""
	Check if user is authenticated.
	Returns current user info if authenticated.
	Also verifies account status and logs out suspended/deactivated users.
	"""
	if request.user.is_authenticated:
		try:
			mail_account = MailAccount.objects.get(user=request.user)

			# Check account status - log out if not active
			account_status = getattr(mail_account, 'status', 'active')
			if account_status != 'active':
				logout(request)
				return JsonResponse({
					'authenticated': False,
					'error': f'Your account has been {account_status}. Please contact an administrator.',
					'reason': account_status
				})

			return JsonResponse({
				'authenticated': True,
				'user': {
					'id': mail_account.id,
					'email': mail_account.email,
					'username': mail_account.username,
					'first_name': mail_account.first_name,
					'last_name': mail_account.last_name,
					'is_admin': mail_account.is_admin,
					'picture': mail_account.picture.url if mail_account.picture else None,
				}
			})
		except MailAccount.DoesNotExist:
			return JsonResponse({
				'authenticated': True,
				'user': {
					'email': request.user.email,
					'username': request.user.username,
				}
			})
	else:
		return JsonResponse({
			'authenticated': False
		})


@require_http_methods(["GET"])
def setup_check(request):
	"""
	Check if initial setup is required.
	Returns True if no MailAccount users exist.
	"""
	needs_setup = not MailAccount.objects.exists()

	return JsonResponse({
		'needsSetup': needs_setup,
		'userCount': MailAccount.objects.count()
	})


@require_http_methods(["POST"])
def register(request):
	"""
	Registration endpoint.
	Only allowed when self-registration is enabled (admins are created via setup).
	"""
	# Only allow registration during initial setup or if explicitly enabled
	from dockspace.core.models import AppSettings
	app_settings = AppSettings.load()
	if not app_settings.allow_registration:
		return JsonResponse({
			'success': False,
			'error': 'Registration is disabled. Contact an administrator.'
		}, status=403)

	try:
		data = json.loads(request.body)
		email = data.get('email', '').strip().lower()
		password = data.get('password', '')
		first_name = data.get('first_name', '').strip()
		last_name = data.get('last_name', '').strip()
		username = data.get('username', '').strip().lower() or email.split('@')[0]

		# Validate required fields
		if not all([email, password, first_name]):
			return JsonResponse({
				'success': False,
				'error': 'Email, password, and first name are required'
			}, status=400)

		# Validate password length (must be at least 12 characters)
		if len(password) < 12:
			return JsonResponse({
				'success': False,
				'error': 'Password must be at least 12 characters long'
			}, status=400)

		# Run Django's password validators (from forms.py MailAccountCreateForm)
		try:
			validate_password(password)
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': ', '.join(e.messages)
			}, status=400)

		# Check if email already exists
		if MailAccount.objects.filter(email__iexact=email).exists():
			return JsonResponse({
				'success': False,
				'error': 'Email already registered'
			}, status=400)

		# Check if username already exists
		if MailAccount.objects.filter(username__iexact=username).exists():
			return JsonResponse({
				'success': False,
				'error': 'Username already taken'
			}, status=400)

		# Create MailAccount (self-registered users are not admins)
		mail_account = MailAccount(
			email=email,
			username=username,
			first_name=first_name,
			last_name=last_name,
			is_admin=False,
		)
		mail_account.set_password(password)

		# Run model validation
		exclude_fields = []
		if not last_name:
			exclude_fields.append('last_name')
		try:
			mail_account.full_clean(exclude=exclude_fields)
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		mail_account.save()

		# Log account registration
		log_action(
			action='account.create',
			request=request,
			target_type='MailAccount',
			target_id=mail_account.id,
			target_name=mail_account.email,
			description=f'User self-registered: {mail_account.email}',
			severity='info',
			success=True
		)

		# Automatically log in the user
		user = authenticate(request, username=email, password=password)
		if user:
			login(request, user)
			audit_login_attempt(request, email, True)
			# Track this login session
			try:
				create_or_update_session(request, mail_account)
			except Exception as e:
				import logging
				logger = logging.getLogger(__name__)
				logger.error(f"Failed to track session: {e}")

		return JsonResponse({
			'success': True,
			'message': 'Account created successfully',
			'user': {
				'id': mail_account.id,
				'email': mail_account.email,
				'username': mail_account.username,
				'first_name': mail_account.first_name,
				'last_name': mail_account.last_name,
				'is_admin': mail_account.is_admin,
				'picture': mail_account.picture.url if mail_account.picture else None,
			}
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


@require_http_methods(["POST"])
def setup_complete(request):
	"""
	Complete initial setup: create admin account and configure app settings.
	Only allowed when no users exist.
	"""
	# Check if this is initial setup
	if MailAccount.objects.exists():
		return JsonResponse({
			'success': False,
			'error': 'Setup already completed'
		}, status=403)

	try:
		data = json.loads(request.body)

		# User account fields
		email = data.get('email', '').strip().lower()
		password = data.get('password', '')
		first_name = data.get('first_name', '').strip()
		last_name = data.get('last_name', '').strip()
		username = data.get('username', '').strip().lower() or email.split('@')[0]

		# App settings fields
		session_timeout = data.get('session_timeout', 86400)  # Default 24 hours
		domain_url = data.get('domain_url', '').strip()

		# Validate required fields
		if not all([email, password, first_name, last_name, domain_url]):
			return JsonResponse({
				'success': False,
				'error': 'All fields are required'
			}, status=400)

		# Validate password length (must be at least 12 characters)
		if len(password) < 12:
			return JsonResponse({
				'success': False,
				'error': 'Password must be at least 12 characters long'
			}, status=400)

		# Run Django's password validators (same as forms.py MailAccountCreateForm)
		try:
			validate_password(password)
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': ', '.join(e.messages)
			}, status=400)

		# Validate session timeout (minimum 5 minutes = 300 seconds)
		if session_timeout < 300:
			return JsonResponse({
				'success': False,
				'error': 'Session timeout must be at least 5 minutes (300 seconds)'
			}, status=400)

		# Check if email already exists
		if MailAccount.objects.filter(email__iexact=email).exists():
			return JsonResponse({
				'success': False,
				'error': 'Email already registered'
			}, status=400)

		# Check if username already exists
		if MailAccount.objects.filter(username__iexact=username).exists():
			return JsonResponse({
				'success': False,
				'error': 'Username already taken'
			}, status=400)

		# Create admin account
		mail_account = MailAccount(
			email=email,
			username=username,
			first_name=first_name,
			last_name=last_name,
			is_admin=True,  # First user is admin
		)
		mail_account.set_password(password)

		# Run model validation
		try:
			mail_account.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		mail_account.save()

		# Configure app settings
		app_settings = AppSettings.load()
		app_settings.session_timeout = session_timeout
		app_settings.domain_url = domain_url.rstrip('/')  # Remove trailing slash

		# Validate app settings
		try:
			app_settings.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': f'Invalid app settings: {str(e)}'
			}, status=400)

		app_settings.save()

		# Log initial setup completion
		log_action(
			action='account.create',
			request=request,
			target_type='MailAccount',
			target_id=mail_account.id,
			target_name=mail_account.email,
			description=f'Initial setup completed: Admin account created ({mail_account.email})',
			severity='info',
			success=True
		)

		log_action(
			action='settings.update',
			request=request,
			target_type='AppSettings',
			target_id=1,
			target_name='Application Settings',
			description='Initial app settings configured',
			metadata={'domain_url': domain_url, 'session_timeout': session_timeout},
			severity='info',
			success=True
		)

		# Automatically log in the user
		user = authenticate(request, username=email, password=password)
		if user:
			login(request, user)
			audit_login_attempt(request, email, True)
			# Track this login session
			try:
				create_or_update_session(request, mail_account)
			except Exception as e:
				import logging
				logger = logging.getLogger(__name__)
				logger.error(f"Failed to track session: {e}")

		return JsonResponse({
			'success': True,
			'message': 'Setup completed successfully',
			'user': {
				'id': mail_account.id,
				'email': mail_account.email,
				'username': mail_account.username,
				'first_name': mail_account.first_name,
				'last_name': mail_account.last_name,
				'is_admin': mail_account.is_admin,
				'picture': mail_account.picture.url if mail_account.picture else None,
			}
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
