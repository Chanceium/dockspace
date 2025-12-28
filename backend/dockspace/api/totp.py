"""
TOTP / Two-Factor Authentication API endpoints.
Handles TOTP device creation, verification, and management.
"""
import json
import pyotp
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from dockspace.core.models import MailAccount, TOTPDevice
from dockspace.api.decorators import json_login_required
from dockspace.api.audit_helpers import log_action, audit_2fa_change


def cleanup_unverified_devices(account):
	"""
	Remove unverified TOTP devices older than 15 minutes.
	Industry standard: Unverified devices should expire to prevent database clutter.
	"""
	cutoff_time = timezone.now() - timedelta(minutes=15)
	TOTPDevice.objects.filter(
		account=account,
		verified_at__isnull=True,
		created_at__lt=cutoff_time
	).delete()


@json_login_required
@require_http_methods(["GET"])
def list_devices(request):
	"""List all TOTP devices for the current user."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Clean up old unverified devices
	cleanup_unverified_devices(mail_account)

	devices = TOTPDevice.objects.filter(account=mail_account)
	device_list = [{
		'id': device.id,
		'name': device.name,
		'verified_at': device.verified_at.isoformat() if device.verified_at else None,
		'last_used_at': device.last_used_at.isoformat() if device.last_used_at else None,
		'created_at': device.created_at.isoformat() if device.created_at else None,
	} for device in devices]

	return JsonResponse({
		'success': True,
		'devices': device_list,
		'has_totp': len(device_list) > 0
	})


@json_login_required
@require_http_methods(["POST"])
def create_device(request):
	"""Create a new TOTP device."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		# Clean up old unverified devices before creating new one
		cleanup_unverified_devices(mail_account)

		data = json.loads(request.body)
		device_name = data.get('name', '').strip()

		if not device_name:
			return JsonResponse({
				'success': False,
				'error': 'Device name is required'
			}, status=400)

		# Check if verified device with this name already exists
		if TOTPDevice.objects.filter(account=mail_account, name=device_name, verified_at__isnull=False).exists():
			return JsonResponse({
				'success': False,
				'error': 'A verified device with this name already exists'
			}, status=400)

		# Generate new TOTP secret
		secret = pyotp.random_base32()

		# Generate provisioning URI for QR code
		totp = pyotp.TOTP(secret)
		provisioning_uri = totp.provisioning_uri(
			name=f"{mail_account.email} - {device_name}",
			issuer_name='Dockspace'
		)

		# Create unverified device (verification happens in verify_device)
		device = TOTPDevice.objects.create(
			account=mail_account,
			name=device_name,
			secret=secret,
			verified_at=None
		)

		return JsonResponse({
			'success': True,
			'device': {
				'id': device.id,
				'name': device.name,
				'secret': secret,
				'provisioning_uri': provisioning_uri,
			},
			'message': 'TOTP device created. Please verify with a token.'
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
def verify_device(request):
	"""Verify a TOTP device with a token."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		data = json.loads(request.body)
		device_id = data.get('device_id')
		token = data.get('token', '').strip()

		if not device_id:
			return JsonResponse({
				'success': False,
				'error': 'Device ID is required'
			}, status=400)

		if not token:
			return JsonResponse({
				'success': False,
				'error': 'Token is required'
			}, status=400)

		# Get device
		try:
			device = TOTPDevice.objects.get(id=device_id, account=mail_account)
		except TOTPDevice.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Device not found'
			}, status=404)

		# Verify token
		totp = pyotp.TOTP(device.secret)
		if totp.verify(token, valid_window=1):
			device.verified_at = timezone.now()
			device.last_used_at = timezone.now()
			device.save()

			# Check if this is the first verified device (2FA being enabled)
			other_verified = TOTPDevice.objects.filter(
				account=mail_account,
				verified_at__isnull=False
			).exclude(id=device.id).count()

			if other_verified == 0:
				# First device - 2FA is being enabled
				audit_2fa_change(request, mail_account, enabled=True)
			else:
				# Additional device
				log_action(
					action='auth.2fa_device_added',
					request=request,
					target_type='MailAccount',
					target_id=mail_account.id,
					target_name=mail_account.email,
					description=f'2FA device verified: {device.name}',
					metadata={'device_name': device.name},
					severity='info',
					success=True
				)

			return JsonResponse({
				'success': True,
				'message': 'Device verified successfully'
			})
		else:
			return JsonResponse({
				'success': False,
				'error': 'Invalid token'
			}, status=400)

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
def delete_device(request, device_id):
	"""Delete a TOTP device."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		device = TOTPDevice.objects.get(id=device_id, account=mail_account)
	except TOTPDevice.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Device not found'
		}, status=404)

	device_name = device.name
	was_verified = device.verified_at is not None
	device.delete()

	# Check if this was the last verified device (2FA being disabled)
	if was_verified:
		remaining_verified = TOTPDevice.objects.filter(
			account=mail_account,
			verified_at__isnull=False
		).count()

		if remaining_verified == 0:
			# Last device - 2FA is being disabled
			audit_2fa_change(request, mail_account, enabled=False)
		else:
			# Still have other devices
			log_action(
				action='auth.2fa_device_removed',
				request=request,
				target_type='MailAccount',
				target_id=mail_account.id,
				target_name=mail_account.email,
				description=f'2FA device removed: {device_name}',
				metadata={'device_name': device_name},
				severity='info',
				success=True
			)

	return JsonResponse({
		'success': True,
		'message': f'Device "{device_name}" deleted successfully'
	})


@json_login_required
@require_http_methods(["GET"])
def get_totp_status(request):
	"""Check if user has two-factor authentication enabled."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Clean up old unverified devices
	cleanup_unverified_devices(mail_account)

	verified_devices = TOTPDevice.objects.filter(
		account=mail_account,
		verified_at__isnull=False
	).count()

	return JsonResponse({
		'success': True,
		'enabled': verified_devices > 0,
		'device_count': verified_devices
	})


# Legacy endpoints for backward compatibility
@require_http_methods(["POST"])
def generate_totp(request):
	"""Legacy endpoint - redirects to create_device."""
	return create_device(request)


@require_http_methods(["POST"])
def verify_totp(request):
	"""Legacy endpoint - redirects to verify_device."""
	return verify_device(request)


@json_login_required
@require_http_methods(["POST"])
def disable_totp(request):
	"""Legacy endpoint - deletes all devices."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Delete all TOTP devices
	count = TOTPDevice.objects.filter(account=mail_account).count()
	verified_count = TOTPDevice.objects.filter(account=mail_account, verified_at__isnull=False).count()
	TOTPDevice.objects.filter(account=mail_account).delete()

	# Log 2FA disable if there were verified devices
	if verified_count > 0:
		audit_2fa_change(request, mail_account, enabled=False)

	return JsonResponse({
		'success': True,
		'message': f'Two-factor authentication disabled ({count} device(s) removed)'
	})
