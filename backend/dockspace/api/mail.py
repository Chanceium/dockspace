"""
Mail management API endpoints.
Handles accounts, quotas, aliases, and groups.
"""
import json
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dockspace.api.decorators import json_login_required, json_admin_required
from dockspace.core.models import MailAccount, MailAlias, MailGroup, MailQuota
from dockspace.api.audit_helpers import log_action, audit_account_status_change


# ============================================================================
# Mail Accounts API
# ============================================================================

@json_admin_required
@require_http_methods(["GET"])
def list_accounts(request):
	"""List all mail accounts (admin only)."""
	accounts = MailAccount.objects.all().order_by('-created_at')
	account_list = []

	for account in accounts:
		# Get alias count
		alias_count = account.mail_aliases.count()

		# Get group count
		group_count = account.mail_groups.count()

		# Get quota
		quota_display = None
		try:
			mail_quota = account.mail_quota
			quota_display = mail_quota.quota_string
		except:
			quota_display = 'No quota set'

		account_list.append({
			'id': account.id,
			'email': account.email,
			'username': account.username,
			'first_name': account.first_name,
			'last_name': account.last_name,
			'is_admin': account.is_admin,
			'status': getattr(account, 'status', 'active'),
			'created_at': account.created_at.isoformat() if account.created_at else None,
			'alias_count': alias_count,
			'group_count': group_count,
			'quota': quota_display,
		})

	return JsonResponse({
		'success': True,
		'accounts': account_list
	})


@json_admin_required
@require_http_methods(["POST"])
def create_account(request):
	"""Create a new mail account (admin only)."""
	try:
		data = json.loads(request.body)
		email = data.get('email', '').strip().lower()
		username = data.get('username', '').strip().lower()
		password = data.get('password', '')
		first_name = data.get('first_name', '').strip()
		last_name = data.get('last_name', '').strip()
		is_admin = data.get('is_admin', False)

		# Validate required fields
		if not all([email, username, password]):
			return JsonResponse({
				'success': False,
				'error': 'email, username, and password are required'
			}, status=400)

		# Validate password
		if len(password) < 12:
			return JsonResponse({
				'success': False,
				'error': 'Password must be at least 12 characters long'
			}, status=400)

		try:
			password_validation.validate_password(password)
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

		# Create MailAccount
		mail_account = MailAccount(
			email=email,
			username=username,
			first_name=first_name,
			last_name=last_name or '',
			is_admin=is_admin,
		)
		mail_account.set_password(password)

		# Run model validation
		exclude_fields = ['last_name'] if not last_name else []
		try:
			mail_account.full_clean(exclude=exclude_fields)
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		mail_account.save()

		# Log account creation
		log_action(
			action='account.create',
			request=request,
			target_type='MailAccount',
			target_id=mail_account.id,
			target_name=mail_account.email,
			description=f'Mail account created: {mail_account.email}',
			metadata={'is_admin': is_admin, 'username': username},
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Account created successfully',
			'account': {
				'id': mail_account.id,
				'email': mail_account.email,
				'username': mail_account.username,
				'first_name': mail_account.first_name,
				'last_name': mail_account.last_name,
				'is_admin': mail_account.is_admin,
				'status': getattr(mail_account, 'status', 'active'),
				'created_at': mail_account.created_at.isoformat() if mail_account.created_at else None,
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
@require_http_methods(["POST"])
def reset_account_password(request, account_id):
	"""
	Reset password for a mail account (admin only).
	- Cannot reset for other admins.
	- Cannot reset your own password.
	"""
	try:
		target_account = MailAccount.objects.get(id=account_id)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		request_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Requesting account not found'
		}, status=404)

	if request_account.id == target_account.id:
		return JsonResponse({
			'success': False,
			'error': 'You cannot reset your own password here.'
		}, status=403)

	if target_account.is_admin:
		return JsonResponse({
			'success': False,
			'error': 'You cannot reset another admin’s password.'
		}, status=403)

	try:
		data = json.loads(request.body)
		new_password = data.get('password', '')

		if len(new_password) < 12:
			return JsonResponse({
				'success': False,
				'error': 'Password must be at least 12 characters long'
			}, status=400)

		try:
			password_validation.validate_password(new_password, user=target_account)
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': ', '.join(e.messages)
			}, status=400)

		target_account.set_password(new_password)
		target_account.save()

		log_action(
			action='account.password_change',
			request=request,
			target_type='MailAccount',
			target_id=target_account.id,
			target_name=target_account.email,
			description=f'Password reset by admin for {target_account.email}',
			metadata={'reset_by_admin': True},
			severity='warning',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Password reset successfully'
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
@require_http_methods(["POST"])
def update_account(request, account_id):
	"""Update a mail account (admin only)."""
	try:
		data = json.loads(request.body)

		try:
			mail_account = MailAccount.objects.get(id=account_id)
		except MailAccount.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Account not found'
			}, status=404)

		# Track changes for audit log
		changed_fields = {}
		old_status = getattr(mail_account, 'status', 'active')
		status_changed = False

		# Update allowed fields
		if 'first_name' in data:
			if mail_account.first_name != data['first_name']:
				changed_fields['first_name'] = {'old': mail_account.first_name, 'new': data['first_name']}
			mail_account.first_name = data['first_name']
		if 'last_name' in data:
			if mail_account.last_name != data['last_name']:
				changed_fields['last_name'] = {'old': mail_account.last_name, 'new': data['last_name']}
			mail_account.last_name = data['last_name']
		if 'is_admin' in data:
			if mail_account.is_admin != data['is_admin']:
				changed_fields['is_admin'] = {'old': mail_account.is_admin, 'new': data['is_admin']}
			mail_account.is_admin = data['is_admin']
		if 'status' in data:
			# Ensure status field exists (may need migration)
			if hasattr(mail_account, 'status'):
				new_status = data['status']
				# Prevent suspending already deactivated accounts
				if getattr(mail_account, 'status', None) == getattr(mail_account, 'STATUS_DEACTIVATED', 'deactivated') and new_status == getattr(mail_account, 'STATUS_SUSPENDED', 'suspended'):
					return JsonResponse({
						'success': False,
						'error': 'Cannot suspend a deactivated account'
					}, status=400)
				if old_status != new_status:
					status_changed = True
				mail_account.status = new_status

		# Validate
		try:
			mail_account.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		mail_account.save()

		# Log status change separately if it occurred
		if status_changed:
			audit_account_status_change(request, mail_account, data['status'], old_status)

		# Log general account update
		if changed_fields or not status_changed:
			log_action(
				action='account.update',
				request=request,
				target_type='MailAccount',
				target_id=mail_account.id,
				target_name=mail_account.email,
				description=f'Account updated: {mail_account.email}',
				metadata={'changed_fields': changed_fields} if changed_fields else {},
				severity='info',
				success=True
			)

		return JsonResponse({
			'success': True,
			'message': 'Account updated successfully'
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
@require_http_methods(["POST"])
def delete_account(request, account_id):
	"""Delete a mail account (admin only)."""
	try:
		mail_account = MailAccount.objects.get(id=account_id)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Prevent deleting self
	try:
		current_account = MailAccount.objects.get(user=request.user)
		if current_account.id == account_id:
			return JsonResponse({
				'success': False,
				'error': 'Cannot delete your own account'
			}, status=400)
	except MailAccount.DoesNotExist:
		pass

	# Prevent deleting other admin accounts
	if mail_account.is_admin:
		return JsonResponse({
			'success': False,
			'error': 'Cannot delete another administrator account'
		}, status=400)

	email = mail_account.email
	account_id = mail_account.id
	mail_account.delete()

	# Log account deletion
	log_action(
		action='account.delete',
		request=request,
		target_type='MailAccount',
		target_id=account_id,
		target_name=email,
		description=f'Account deleted: {email}',
		severity='warning',
		success=True
	)

	return JsonResponse({
		'success': True,
		'message': f'Account "{email}" deleted successfully'
	})


# ============================================================================
# Mail Quota API
# ============================================================================

@json_admin_required
@require_http_methods(["GET"])
def list_quotas(request):
	"""List all mail quotas (admin only)."""
	quotas = MailQuota.objects.select_related('user').all()
	quota_list = [{
		'id': q.id,
		'user_id': q.user.id,
		'user_email': q.user.email,
		'size_value': q.size_value,
		'suffix': q.suffix,
		'quota_string': q.quota_string,
	} for q in quotas]

	return JsonResponse({
		'success': True,
		'quotas': quota_list
	})


@json_login_required
@require_http_methods(["GET"])
def get_quota(request, account_id):
	"""Get quota for a specific account."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Users can view their own quota, admins can view any
	if not mail_account.is_admin and mail_account.id != int(account_id):
		return JsonResponse({
			'success': False,
			'error': 'Permission denied'
		}, status=403)

	try:
		target_account = MailAccount.objects.get(id=account_id)
		quota = MailQuota.objects.get(user=target_account)
		return JsonResponse({
			'success': True,
			'quota': {
				'id': quota.id,
				'user_id': quota.user.id,
				'user_email': quota.user.email,
				'size_value': quota.size_value,
				'suffix': quota.suffix,
				'quota_string': quota.quota_string,
			}
		})
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)
	except MailQuota.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'No quota set for this account'
		}, status=404)


@json_admin_required
@require_http_methods(["POST"])
def create_quota(request):
	"""Create or update quota for an account (admin only)."""
	try:
		data = json.loads(request.body)
		user_id = data.get('user_id')
		size_value = data.get('size_value')
		suffix = data.get('suffix', 'G')

		if not user_id or not size_value:
			return JsonResponse({
				'success': False,
				'error': 'user_id and size_value are required'
			}, status=400)

		if size_value <= 0:
			return JsonResponse({
				'success': False,
				'error': 'Quota size must be greater than zero'
			}, status=400)

		try:
			target_account = MailAccount.objects.get(id=user_id)
		except MailAccount.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Target account not found'
			}, status=404)

		# Create or update quota
		quota, created = MailQuota.objects.update_or_create(
			user=target_account,
			defaults={
				'size_value': size_value,
				'suffix': suffix,
			}
		)

		# Validate
		try:
			quota.full_clean()
		except ValidationError as e:
			quota.delete() if created else None
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		# Log quota change
		log_action(
			action='quota.update',
			request=request,
			target_type='MailAccount',
			target_id=target_account.id,
			target_name=target_account.email,
			description=f'Quota {"created" if created else "updated"} for {target_account.email}: {quota.quota_string}',
			metadata={'size_value': size_value, 'suffix': suffix},
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': f'Quota {"created" if created else "updated"} successfully',
			'quota': {
				'id': quota.id,
				'user_id': quota.user.id,
				'user_email': quota.user.email,
				'size_value': quota.size_value,
				'suffix': quota.suffix,
				'quota_string': quota.quota_string,
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
@require_http_methods(["DELETE"])
def delete_quota(request, quota_id):
	"""Delete a mail quota (admin only)."""
	try:
		quota = MailQuota.objects.get(id=quota_id)
		user_email = quota.user.email
		user_id = quota.user.id
		quota.delete()

		# Log quota deletion
		log_action(
			action='quota.delete',
			request=request,
			target_type='MailAccount',
			target_id=user_id,
			target_name=user_email,
			description=f'Quota removed for {user_email}',
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Quota deleted successfully'
		})
	except MailQuota.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Quota not found'
		}, status=404)


# ============================================================================
# Mail Alias API
# ============================================================================

@json_login_required
@require_http_methods(["GET"])
def list_aliases(request):
	"""List mail aliases for current user or all (if admin)."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	if mail_account.is_admin:
		aliases = MailAlias.objects.select_related('user').all()
	else:
		aliases = MailAlias.objects.filter(user=mail_account)

	alias_list = [{
		'id': a.id,
		'alias_email': a.alias,
		'destination_email': a.user.email,
		'user_id': a.user.id,
		'user_email': a.user.email,
		'created_at': a.created_at.isoformat() if getattr(a, 'created_at', None) else None,
	} for a in aliases]

	return JsonResponse({
		'success': True,
		'aliases': alias_list
	})


@json_login_required
@require_http_methods(["POST"])
def create_alias(request):
	"""Create a mail alias for the current user or any user (if admin)."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		data = json.loads(request.body)
		alias_email = (data.get('alias_email') or data.get('alias') or '').strip().lower()
		destination_email = (data.get('destination_email') or '').strip().lower()
		user_id = data.get('user_id')

		if not alias_email:
			return JsonResponse({
				'success': False,
				'error': 'Alias email is required'
			}, status=400)

		# Determine target user
		target_user = None
		if destination_email:
			try:
				target_user = MailAccount.objects.get(email__iexact=destination_email)
			except MailAccount.DoesNotExist:
				return JsonResponse({
					'success': False,
					'error': 'Destination account not found'
				}, status=404)

			if not mail_account.is_admin and target_user.id != mail_account.id:
				return JsonResponse({
					'success': False,
					'error': 'Only admins can create aliases for other users'
				}, status=403)
		elif user_id:
			if not mail_account.is_admin:
				return JsonResponse({
					'success': False,
					'error': 'Only admins can create aliases for other users'
				}, status=403)
			try:
				target_user = MailAccount.objects.get(id=user_id)
			except MailAccount.DoesNotExist:
				return JsonResponse({
					'success': False,
					'error': 'Target user not found'
				}, status=404)
		else:
			target_user = mail_account

		# Create alias
		alias = MailAlias(alias=alias_email, user=target_user)

		# Validate
		try:
			alias.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		alias.save()

		# Log alias creation
		log_action(
			action='alias.create',
			request=request,
			target_type='MailAlias',
			target_id=alias.id,
			target_name=alias.alias,
			description=f'Alias created: {alias.alias} → {alias.user.email}',
			metadata={'destination': alias.user.email},
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Alias created successfully',
			'alias': {
				'id': alias.id,
				'alias_email': alias.alias,
				'destination_email': alias.user.email,
				'user_id': alias.user.id,
				'user_email': alias.user.email,
				'created_at': alias.created_at.isoformat() if getattr(alias, 'created_at', None) else None,
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


@json_login_required
@require_http_methods(["DELETE"])
def delete_alias(request, alias_id):
	"""Delete a mail alias."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		alias = MailAlias.objects.get(id=alias_id)

		# Users can only delete their own aliases, admins can delete any
		if not mail_account.is_admin and alias.user.id != mail_account.id:
			return JsonResponse({
				'success': False,
				'error': 'Permission denied'
			}, status=403)

		alias_email = alias.alias
		dest_email = alias.user.email
		alias.delete()

		# Log alias deletion
		log_action(
			action='alias.delete',
			request=request,
			target_type='MailAlias',
			target_id=alias_id,
			target_name=alias_email,
			description=f'Alias deleted: {alias_email} → {dest_email}',
			metadata={'destination': dest_email},
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Alias deleted successfully'
		})
	except MailAlias.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Alias not found'
		}, status=404)


# ============================================================================
# Mail Group API
# ============================================================================

@json_login_required
@require_http_methods(["GET"])
def list_groups(request):
	"""List mail groups for current user or all (if admin)."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	if mail_account.is_admin:
		groups = MailGroup.objects.all()
	else:
		groups = MailGroup.objects.filter(members=mail_account)

	group_list = [{
		'id': g.id,
		'name': g.name,
		'member_count': g.members.count(),
		'created_at': g.created_at.isoformat() if getattr(g, 'created_at', None) else None,
		'updated_at': g.updated_at.isoformat() if getattr(g, 'updated_at', None) else None,
	} for g in groups]

	return JsonResponse({
		'success': True,
		'groups': group_list
	})


@json_login_required
@require_http_methods(["GET"])
def get_group(request, group_id):
	"""Get details of a specific mail group."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	try:
		group = MailGroup.objects.get(id=group_id)
		members = [{
			'id': m.id,
			'email': m.email,
			'username': m.username,
			'first_name': m.first_name,
			'last_name': m.last_name,
		} for m in group.members.all()]

		return JsonResponse({
			'success': True,
			'group': {
				'id': group.id,
				'name': group.name,
				'members': members,
			}
		})
	except MailGroup.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Group not found'
		}, status=404)


@json_admin_required
@require_http_methods(["POST"])
def create_group(request):
	"""Create a new mail group (admin only)."""
	try:
		data = json.loads(request.body)
		name = data.get('name', '').strip()

		if not name:
			return JsonResponse({
				'success': False,
				'error': 'Group name is required'
			}, status=400)

		# Check if group name already exists
		if MailGroup.objects.filter(name__iexact=name).exists():
			return JsonResponse({
				'success': False,
				'error': 'Group name already exists'
			}, status=400)

		group = MailGroup(name=name)

		# Validate
		try:
			group.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		group.save()

		# Log group creation
		log_action(
			action='group.create',
			request=request,
			target_type='MailGroup',
			target_id=group.id,
			target_name=group.name,
			description=f'Group created: {group.name}',
			severity='info',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Group created successfully',
			'group': {
				'id': group.id,
				'name': group.name,
				'member_count': 0,
				'created_at': group.created_at.isoformat() if getattr(group, 'created_at', None) else None,
				'updated_at': group.updated_at.isoformat() if getattr(group, 'updated_at', None) else None,
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
@require_http_methods(["PUT", "PATCH"])
def update_group(request, group_id):
	"""Update a mail group (admin only)."""
	try:
		group = MailGroup.objects.get(id=group_id)
	except MailGroup.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Group not found'
		}, status=404)

	try:
		data = json.loads(request.body)
		name = data.get('name', '').strip()
		old_name = group.name

		if name:
			# Check if new name conflicts with existing group
			if MailGroup.objects.filter(name__iexact=name).exclude(id=group_id).exists():
				return JsonResponse({
					'success': False,
					'error': 'Group name already exists'
				}, status=400)
			group.name = name

		# Validate
		try:
			group.full_clean()
		except ValidationError as e:
			return JsonResponse({
				'success': False,
				'error': str(e)
			}, status=400)

		group.save()

		# Log group update
		if old_name != group.name:
			log_action(
				action='group.update',
				request=request,
				target_type='MailGroup',
				target_id=group.id,
				target_name=group.name,
				description=f'Group renamed: {old_name} → {group.name}',
				metadata={'old_name': old_name, 'new_name': group.name},
				severity='info',
				success=True
			)

		return JsonResponse({
			'success': True,
			'message': 'Group updated successfully'
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
def delete_group(request, group_id):
	"""Delete a mail group (admin only)."""
	try:
		group = MailGroup.objects.get(id=group_id)
		group_name = group.name
		member_count = group.members.count()
		group.delete()

		# Log group deletion
		log_action(
			action='group.delete',
			request=request,
			target_type='MailGroup',
			target_id=group_id,
			target_name=group_name,
			description=f'Group deleted: {group_name} ({member_count} members)',
			metadata={'member_count': member_count},
			severity='warning',
			success=True
		)

		return JsonResponse({
			'success': True,
			'message': 'Group deleted successfully'
		})
	except MailGroup.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Group not found'
		}, status=404)


# ============================================================================
# Account Groups API (Assign groups to accounts)
# ============================================================================

@json_login_required
@require_http_methods(["GET"])
def get_account_groups(request, account_id):
	"""Get groups for a specific account."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Users can view their own groups, admins can view any
	if not mail_account.is_admin and mail_account.id != int(account_id):
		return JsonResponse({
			'success': False,
			'error': 'Permission denied'
		}, status=403)

	try:
		target_account = MailAccount.objects.get(id=account_id)
		groups = [{
			'id': g.id,
			'name': g.name,
		} for g in target_account.mail_groups.all()]

		return JsonResponse({
			'success': True,
			'account_id': target_account.id,
			'account_email': target_account.email,
			'groups': groups
		})
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)


@json_admin_required
@require_http_methods(["POST"])
def update_account_groups(request, account_id):
	"""Update group memberships for an account (admin only)."""
	try:
		target_account = MailAccount.objects.get(id=account_id)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Target account not found'
		}, status=404)

	try:
		data = json.loads(request.body)
		group_ids = data.get('group_ids', [])

		# Validate all group IDs exist
		groups = MailGroup.objects.filter(id__in=group_ids)
		if len(groups) != len(group_ids):
			return JsonResponse({
				'success': False,
				'error': 'One or more group IDs are invalid'
			}, status=400)

		# Get old groups for logging
		old_groups = set(target_account.mail_groups.values_list('id', flat=True))
		new_groups = set(group_ids)

		# Update groups
		target_account.mail_groups.set(groups)

		# Log group membership changes
		added_groups = new_groups - old_groups
		removed_groups = old_groups - new_groups

		if added_groups or removed_groups:
			group_names = {g.id: g.name for g in MailGroup.objects.filter(id__in=list(added_groups) + list(removed_groups))}
			log_action(
				action='group.members_update',
				request=request,
				target_type='MailAccount',
				target_id=target_account.id,
				target_name=target_account.email,
				description=f'Group memberships updated for {target_account.email}',
				metadata={
					'added_groups': [group_names.get(gid, f'Group {gid}') for gid in added_groups],
					'removed_groups': [group_names.get(gid, f'Group {gid}') for gid in removed_groups]
				},
				severity='info',
				success=True
			)

		return JsonResponse({
			'success': True,
			'message': 'Account groups updated successfully'
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
