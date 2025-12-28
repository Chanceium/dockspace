"""
User profile API endpoints.
Handles user profile viewing and editing.
"""
import json
from datetime import datetime
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse
from django.utils.module_loading import import_string
from django.views.decorators.http import require_http_methods

from dockspace.core.models import MailAccount
from dockspace.api.decorators import json_login_required
from dockspace.api.audit_helpers import log_action, audit_password_change, audit_account_status_change


@json_login_required
@require_http_methods(["GET"])
def get_profile(request):
	"""Get current user profile."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Get alias count
	alias_count = mail_account.mail_aliases.count()

	# Get group count
	group_count = mail_account.mail_groups.count()

	# Get quota
	quota_display = None
	try:
		mail_quota = mail_account.mail_quota
		quota_display = mail_quota.quota_string
	except:
		quota_display = 'No quota set'

	return JsonResponse({
		'success': True,
		'profile': {
			'id': mail_account.id,
			'email': mail_account.email,
			'username': mail_account.username,
			'first_name': mail_account.first_name,
			'last_name': mail_account.last_name,
			'middle_name': mail_account.middle_name,
			'phone_number': mail_account.phone_number,
			'website': mail_account.website,
			'profile': mail_account.profile,
			'gender': mail_account.gender,
			'birthdate': mail_account.birthdate.isoformat() if mail_account.birthdate else None,
			'zoneinfo': mail_account.zoneinfo,
			'locale': mail_account.locale,
			'street_address': mail_account.street_address,
			'locality': mail_account.locality,
			'region': mail_account.region,
			'postal_code': mail_account.postal_code,
			'country': mail_account.country,
			'picture': mail_account.picture.url if mail_account.picture else None,
			'is_admin': mail_account.is_admin,
			'status': mail_account.status if hasattr(mail_account, 'status') else 'active',
			'created_at': mail_account.created_at.isoformat() if mail_account.created_at else None,
			'alias_count': alias_count,
			'group_count': group_count,
			'quota': quota_display,
		}
	})


@json_login_required
@require_http_methods(["POST"])
def update_profile(request):
	"""Update current user profile."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		data = json.loads(request.body)

		# Update allowed fields
		if 'first_name' in data:
			mail_account.first_name = data['first_name']
		if 'last_name' in data:
			mail_account.last_name = data['last_name']
		if 'middle_name' in data:
			mail_account.middle_name = data['middle_name']
		if 'phone_number' in data:
			mail_account.phone_number = data['phone_number']
		if 'website' in data:
			mail_account.website = data['website']
		if 'profile' in data:
			mail_account.profile = data['profile']
		if 'gender' in data:
			mail_account.gender = data['gender']
		if 'birthdate' in data:
			if data['birthdate']:
				mail_account.birthdate = datetime.fromisoformat(data['birthdate']).date()
			else:
				mail_account.birthdate = None
		if 'zoneinfo' in data:
			mail_account.zoneinfo = data['zoneinfo']
		if 'locale' in data:
			mail_account.locale = data['locale']
		if 'street_address' in data:
			mail_account.street_address = data['street_address']
		if 'locality' in data:
			mail_account.locality = data['locality']
		if 'region' in data:
			mail_account.region = data['region']
		if 'postal_code' in data:
			mail_account.postal_code = data['postal_code']
		if 'country' in data:
			mail_account.country = data['country']

		# Validate
		try:
			mail_account.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		mail_account.save()

		# Log profile update
		log_action(
			action='account.profile_update',
			request=request,
			target_type='MailAccount',
			target_id=mail_account.id,
			target_name=mail_account.email,
			description=f'Profile updated for {mail_account.email}',
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Profile updated successfully'
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


@json_login_required
@require_http_methods(["POST"])
def upload_profile_photo(request):
	"""Upload profile photo for current user."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Check if file was uploaded
	if 'picture' not in request.FILES:
		return JsonResponse({
			'success': False,
			'error': 'No file uploaded'
		}, status=400)

	uploaded_file = request.FILES['picture']

	# Validate file size (max 5MB)
	max_size = 5 * 1024 * 1024  # 5MB
	if uploaded_file.size > max_size:
		return JsonResponse({
			'success': False,
			'error': 'File size exceeds 5MB limit'
		}, status=400)

	# Validate file type
	allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
	if uploaded_file.content_type not in allowed_types:
		return JsonResponse({
			'success': False,
			'error': 'Invalid file type. Only JPEG, PNG, GIF, and WEBP are allowed.'
		}, status=400)

	try:
		# Delete old picture if exists
		if mail_account.picture:
			old_picture = mail_account.picture
			mail_account.picture = None
			mail_account.save()
			# Delete the old file
			if old_picture.name:
				storage = old_picture.storage
				if storage.exists(old_picture.name):
					storage.delete(old_picture.name)

		# Assign new picture (model will process and validate it)
		mail_account.picture = uploaded_file
		mail_account.save()

		# Log profile photo update
		log_action(
			action='account.profile_update',
			request=request,
			target_type='MailAccount',
			target_id=mail_account.id,
			target_name=mail_account.email,
			description=f'Profile photo updated for {mail_account.email}',
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Profile photo updated successfully',
			'picture_url': mail_account.picture.url if mail_account.picture else None
		})

	except ValidationError as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=400)
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': f'Failed to upload photo: {str(e)}'
		}, status=500)


@require_http_methods(["GET"])
def get_password_requirements(request):
	"""
	Get password validation requirements from Django settings.
	Returns a list of human-readable password requirements.
	"""
	requirements = []

	for validator_config in settings.AUTH_PASSWORD_VALIDATORS:
		validator_path = validator_config['NAME']
		validator_options = validator_config.get('OPTIONS', {})

		try:
			# Import the validator class
			validator_class = import_string(validator_path)
			validator_instance = validator_class(**validator_options)

			# Get help text from validator
			if hasattr(validator_instance, 'get_help_text'):
				help_text = validator_instance.get_help_text()
				if help_text:
					requirements.append(help_text)
		except Exception:
			# Skip validators that can't be loaded or don't have help text
			continue

	return JsonResponse({
		'success': True,
		'requirements': requirements
	})


@json_login_required
@require_http_methods(["POST"])
def deactivate_account(request):
	"""Deactivate current user's account and log them out."""
	try:
		try:
			mail_account = MailAccount.objects.get(user=request.user)
		except MailAccount.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Account not found'
			}, status=404)

		# Set status if available, otherwise disable user
		old_status = getattr(mail_account, 'status', 'active')
		if hasattr(mail_account, 'status'):
			mail_account.status = getattr(mail_account, 'STATUS_DEACTIVATED', 'deactivated')
		mail_account.is_active = False
		mail_account.save()

		# Log account deactivation
		audit_account_status_change(request, mail_account, 'deactivated', old_status)

		# Also deactivate the Django User if present
		if request.user:
			request.user.is_active = False
			request.user.save()

		from django.contrib.auth import logout
		logout(request)

		return JsonResponse({
			'success': True,
			'message': 'Account deactivated and logged out'
		})
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		}, status=500)


@json_login_required
@require_http_methods(["POST"])
def change_password(request):
	"""Change user password with validation."""
	import crypt

	try:
		# Get the MailAccount associated with the user
		try:
			mail_account = MailAccount.objects.get(user=request.user)
		except MailAccount.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Account not found'
			}, status=404)

		data = json.loads(request.body)
		current_password = data.get('current_password', '')
		new_password = data.get('new_password', '')

		# Validate inputs
		if not current_password:
			return JsonResponse({
				'success': False,
				'error': 'Current password is required'
			}, status=400)

		if not new_password:
			return JsonResponse({
				'success': False,
				'error': 'New password is required'
			}, status=400)

		# Validate current password against MailAccount's SHA512-CRYPT hash
		stored_hash = mail_account.password_hash
		if stored_hash.startswith("{SHA512-CRYPT}"):
			stored_hash = stored_hash[len("{SHA512-CRYPT}"):]

		candidate_hash = crypt.crypt(current_password, stored_hash)
		if candidate_hash != stored_hash:
			return JsonResponse({
				'success': False,
				'error': 'Current password is incorrect'
			}, status=400)

		# Validate new password using Django's validators
		try:
			password_validation.validate_password(new_password, user=request.user)
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'errors': e.messages
			}, status=400)

		# Set new password on MailAccount (this creates the SHA512-CRYPT hash)
		mail_account.set_password(new_password)
		mail_account.save()

		# Also update the Django User password for consistency
		request.user.set_password(new_password)
		request.user.save()

		# Log password change
		audit_password_change(request, mail_account, changed_by_admin=False)

		return JsonResponse({
			'success': True,
			'message': 'Password changed successfully'
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
