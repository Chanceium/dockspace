"""
OIDC Client management API endpoints.
Handles OIDC client creation, management, and access control (admin only).
"""
import json
import secrets
import string
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dockspace.api.decorators import json_admin_required
from dockspace.core.models import MailAccount, MailGroup, ClientAccess
from dockspace.api.audit_helpers import log_action

try:
	from oidc_provider.models import Client
except Exception:
	Client = None


def _client_datetimes(client):
	created = getattr(client, 'created_at', None) or getattr(client, 'date_created', None)
	updated = getattr(client, 'updated_at', None) or getattr(client, 'date_updated', None) or getattr(client, 'modified_at', None)
	return (
		created.isoformat() if created else None,
		updated.isoformat() if updated else None,
	)


if Client:
	@json_admin_required
	@require_http_methods(["GET"])
	def list_clients(request):
		"""List all OIDC clients (admin only)."""
		clients = Client.objects.all()
		client_list = [{
			'id': c.id,
			'name': c.name,
			'client_id': c.client_id,
			'client_type': 'confidential',
			'response_types': list(c.response_types.all().values_list('value', flat=True)),
			'jwt_alg': c.jwt_alg,
			'redirect_uris': getattr(c, 'redirect_uris', []),
			'scope': ' '.join(c.scope) if hasattr(c, 'scope') else '',
			'created_at': _client_datetimes(c)[0],
			'updated_at': _client_datetimes(c)[1],
			'group_count': ClientAccess.objects.filter(client=c).prefetch_related('groups').first().groups.count() if ClientAccess.objects.filter(client=c).exists() else 0,
			'require_2fa': ClientAccess.objects.filter(client=c).first().require_2fa if ClientAccess.objects.filter(client=c).exists() else False,
		} for c in clients]

		return JsonResponse({
			'success': True,
			'clients': client_list
		})

	@json_admin_required
	@require_http_methods(["GET"])
	def get_client(request, client_id):
		"""Get details of a specific OIDC client (admin only)."""
		try:
			client = Client.objects.get(id=client_id)
			created_at, updated_at = _client_datetimes(client)
			return JsonResponse({
				'success': True,
				'client': {
					'id': client.id,
					'name': client.name,
					'client_id': client.client_id,
					'client_secret': client.client_secret,
					'client_type': 'confidential',
					'response_types': list(client.response_types.all().values_list('value', flat=True)),
					'jwt_alg': client.jwt_alg,
					'redirect_uris': client.redirect_uris,
					'scope': ' '.join(client.scope) if hasattr(client, 'scope') else '',
					'created_at': created_at,
					'updated_at': updated_at,
				}
			})
		except Client.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Client not found'
			}, status=404)

	@json_admin_required
	@require_http_methods(["POST"])
	def create_client(request):
		"""Create a new OIDC client (admin only)."""
		try:
			data = json.loads(request.body)
			name = data.get('name', '').strip()
			client_id = (data.get('client_id') or '').strip()
			client_secret = (data.get('client_secret') or '').strip()
			client_type = 'confidential'
			redirect_uris = data.get('redirect_uris', '').strip()
			jwt_alg = 'RS256'
			response_types = data.get('response_types', ['code'])
			scope = (data.get('scope') or '').strip()
			group_ids = data.get('group_ids', [])
			require_2fa = data.get('require_2fa', False)

			if not name:
				return JsonResponse({
					'success': False,
					'error': 'Client name is required'
				}, status=400)

			allowed_response_types = {
				'code',
				'id_token',
				'id_token token',
				'code token',
				'code id_token',
				'code id_token token',
			}
			response_types = [rt for rt in response_types if rt in allowed_response_types] or ['code']

			def generate_client_id():
				return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(24))

			def generate_client_secret():
				return secrets.token_urlsafe(32)

			if not client_id:
				client_id = generate_client_id()
			if not client_secret:
				client_secret = generate_client_secret()

			if Client.objects.filter(client_id=client_id).exists():
				return JsonResponse({
					'success': False,
					'error': 'This client ID already exists'
				}, status=400)

			# Create client
			client = Client(
				name=name,
				client_id=client_id,
				client_secret=client_secret,
				client_type=client_type,
				jwt_alg=jwt_alg,
				redirect_uris=redirect_uris.split('\n') if redirect_uris else [],
				scope=scope.split() if scope else [],
			)

			# Validate
			try:
				client.full_clean()
			except ValidationError as e:
				return JsonResponse({
					'success': False,
					'error': str(e)
				}, status=400)

			client.save()

			# Handle response_types (ManyToMany)
			if response_types:
				from oidc_provider.models import ResponseType
				for rt_value in response_types:
					rt, _ = ResponseType.objects.get_or_create(value=rt_value)
					client.response_types.add(rt)

			# Handle access control (groups + require 2FA)
			if group_ids:
				groups = MailGroup.objects.filter(id__in=group_ids)
				if len(groups) != len(group_ids):
					return JsonResponse({
						'success': False,
						'error': 'One or more group IDs are invalid'
					}, status=400)
			else:
				groups = []

			client_access, _ = ClientAccess.objects.get_or_create(
				client=client,
				defaults={'require_2fa': require_2fa}
			)
			client_access.require_2fa = require_2fa
			client_access.save()
			client_access.groups.set(groups)

			# Log OIDC client creation
			log_action(
				action='oidc.client_create',
				request=request,
				target_type='OIDCClient',
				target_id=client.id,
				target_name=client.name,
				description=f'OIDC client created: {client.name}',
				metadata={
					'client_id': client.client_id,
					'require_2fa': require_2fa,
					'groups': [g.name for g in groups]
				},
				severity='info',
				success=True
			)

			return JsonResponse({
				'success': True,
				'message': 'OIDC client created successfully',
				'client': {
					'id': client.id,
					'name': client.name,
					'client_id': client.client_id,
					'client_secret': client.client_secret,
					'client_type': client.client_type,
					'response_types': list(client.response_types.all().values_list('value', flat=True)),
					'jwt_alg': client.jwt_alg,
					'redirect_uris': client.redirect_uris,
					'scope': ' '.join(client.scope) if hasattr(client, 'scope') else '',
					'require_2fa': client_access.require_2fa,
					'groups': [{'id': g.id, 'name': g.name} for g in groups],
					'created_at': _client_datetimes(client)[0],
					'updated_at': _client_datetimes(client)[1],
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

	@json_admin_required
	@require_http_methods(["POST", "PUT", "PATCH"])
	def update_client(request, client_id):
		"""Update an OIDC client (admin only)."""
		try:
			client = Client.objects.get(id=client_id)
		except Client.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Client not found'
			}, status=404)

		try:
			data = json.loads(request.body)

			if 'name' in data:
				client.name = data['name']
			if 'client_secret' in data:
				client.client_secret = data['client_secret']
			# client_type is fixed to confidential
			client.client_type = 'confidential'
			# jwt_alg is fixed to RS256 by design
			if 'redirect_uris' in data:
				redirect_uris = data['redirect_uris'].strip()
				client.redirect_uris = redirect_uris.split('\n') if redirect_uris else []
			if 'scope' in data:
				scope = (data.get('scope') or '').strip()
				client.scope = scope.split() if scope else []

			# Validate
			try:
				client.full_clean()
			except ValidationError as e:
				return JsonResponse({
					'success': False,
					'error': str(e)
				}, status=400)

			client.save()

			# Handle response_types update
			if 'response_types' in data:
				from oidc_provider.models import ResponseType
				client.response_types.clear()
				allowed_response_types = {
					'code',
					'id_token',
					'id_token token',
					'code token',
					'code id_token',
					'code id_token token',
				}
				response_types = [rt for rt in data['response_types'] if rt in allowed_response_types] or ['code']
				for rt_value in response_types:
					rt, _ = ResponseType.objects.get_or_create(value=rt_value)
					client.response_types.add(rt)

			# Update access controls if provided
			group_ids = data.get('group_ids')
			require_2fa = data.get('require_2fa')
			if group_ids is not None or require_2fa is not None:
				groups = []
				if group_ids is not None:
					groups = list(MailGroup.objects.filter(id__in=group_ids))
					if len(groups) != len(group_ids):
						return JsonResponse({
							'success': False,
							'error': 'One or more group IDs are invalid'
						}, status=400)

				client_access, _ = ClientAccess.objects.get_or_create(client=client)
				if require_2fa is not None:
					client_access.require_2fa = bool(require_2fa)
					client_access.save()
				if group_ids is not None:
					client_access.groups.set(groups)

			# Log OIDC client update
			log_action(
				action='oidc.client_update',
				request=request,
				target_type='OIDCClient',
				target_id=client.id,
				target_name=client.name,
				description=f'OIDC client updated: {client.name}',
				severity='info',
				success=True
			)

			return JsonResponse({
				'success': True,
				'message': 'OIDC client updated successfully'
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

	@json_admin_required
	@require_http_methods(["DELETE"])
	def delete_client(request, client_id):
		"""Delete an OIDC client (admin only)."""
		try:
			client = Client.objects.get(id=client_id)
			client_name = client.name
			oidc_client_id = client.client_id
			client.delete()

			# Log OIDC client deletion
			log_action(
				action='oidc.client_delete',
				request=request,
				target_type='OIDCClient',
				target_id=client_id,
				target_name=client_name,
				description=f'OIDC client deleted: {client_name}',
				metadata={'client_id': oidc_client_id},
				severity='warning',
				success=True
			)

			return JsonResponse({
				'success': True,
				'message': 'OIDC client deleted successfully'
			})
		except Client.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Client not found'
			}, status=404)


	# ============================================================================
	# Client Access / Groups API
	# ============================================================================

	@json_admin_required
	@require_http_methods(["GET"])
	def get_client_access(request, client_id):
		"""Get access control settings for an OIDC client (admin only)."""
		try:
			client = Client.objects.get(id=client_id)
		except Client.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Client not found'
			}, status=404)

		try:
			client_access = ClientAccess.objects.get(client=client)
			groups = [{
				'id': g.id,
				'name': g.name,
			} for g in client_access.groups.all()]

			return JsonResponse({
				'success': True,
				'client_access': {
					'client_id': client.id,
					'client_name': client.name,
					'require_2fa': client_access.require_2fa,
					'groups': groups,
				}
			})
		except ClientAccess.DoesNotExist:
			return JsonResponse({
				'success': True,
				'client_access': {
					'client_id': client.id,
					'client_name': client.name,
					'require_2fa': False,
					'groups': [],
				}
			})

	@json_admin_required
	@require_http_methods(["POST"])
	def update_client_access(request, client_id):
		"""Update access control settings for an OIDC client (admin only)."""
		try:
			client = Client.objects.get(id=client_id)
		except Client.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Client not found'
			}, status=404)

		try:
			data = json.loads(request.body)
			group_ids = data.get('group_ids', [])
			require_2fa = data.get('require_2fa', False)

			# Validate all group IDs exist
			groups = MailGroup.objects.filter(id__in=group_ids)
			if len(groups) != len(group_ids):
				return JsonResponse({
					'success': False,
					'error': 'One or more group IDs are invalid'
				}, status=400)

			# Get or create ClientAccess
			client_access, created = ClientAccess.objects.get_or_create(
				client=client,
				defaults={'require_2fa': require_2fa}
			)

			if not created:
				client_access.require_2fa = require_2fa
				client_access.save()

			# Update groups
			client_access.groups.set(groups)

			# Log client access update
			log_action(
				action='oidc.access_update',
				request=request,
				target_type='OIDCClient',
				target_id=client.id,
				target_name=client.name,
				description=f'OIDC client access updated: {client.name}',
				metadata={
					'require_2fa': require_2fa,
					'groups': [g.name for g in groups]
				},
				severity='info',
				success=True
			)

			return JsonResponse({
				'success': True,
				'message': 'Client access settings updated successfully'
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

else:
	# Stub endpoints when OIDC provider is not available
	def list_clients(request):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)

	def get_client(request, client_id):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)

	def create_client(request):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)

	def update_client(request, client_id):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)

	def delete_client(request, client_id):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)

	def get_client_access(request, client_id):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)

	def update_client_access(request, client_id):
		return JsonResponse({'success': False, 'error': 'OIDC provider not available'}, status=501)
