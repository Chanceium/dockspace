import base64
import io

import pyotp
import qrcode
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .auth_backend import AccountUserBackend
from .forms import (
	AccountGroupsForm,
	AppSettingsForm,
	MailAccountCreateForm,
	MailAccountProfileForm,
	MailAliasForm,
	MailGroupForm,
	MailQuotaForm,
	ClientGroupsForm,
	TOTPVerifyForm,
	OIDCClientCreateForm,
)
from .models import AppSettings, ClientAccess, MailAccount, MailAlias, MailGroup, MailQuota

try:
	from oidc_provider.models import Client
except Exception:
	Client = None


class AccountLoginForm(forms.Form):
	username = forms.CharField(
		label="Username or email",
		widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
	)
	password = forms.CharField(
		widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
		label="Password",
	)


def account_login(request):
	# If no accounts exist yet, send users to initial registration
	if not MailAccount.objects.exists():
		return redirect("dockspace:account_register")

	if request.user.is_authenticated:
		account = getattr(request.user, "account", None)
		target = reverse("dockspace:management") if getattr(account, "is_admin", False) else reverse("dockspace:account_profile")
		return redirect(target)
	request_next = request.GET.get("next")
	next_url_default = reverse("dockspace:management") if request.user.is_authenticated and getattr(request.user, "account", None) and getattr(request.user.account, "is_admin", False) else reverse("dockspace:account_profile")
	get_token(request)  # ensure CSRF cookie is set
	if request.method == "POST":
		form = AccountLoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data["username"]
			password = form.cleaned_data["password"]

			# Resolve account for staged TOTP flow if token omitted.
			account = MailAccount.objects.filter(username__iexact=username).first() or MailAccount.objects.filter(email__iexact=username).first()
			if account and account.totp_secret:
				backend = AccountUserBackend()
				if backend._verify_sha512(password, account.password_hash):
					request.session["pending_totp_account"] = account.id
					request.session["pending_totp_next"] = request_next or (reverse("dockspace:management") if account.is_admin else reverse("dockspace:account_profile"))
					return redirect("dockspace:account_totp")
			# Fallback: attempt full authentication (with token if provided).
			user = authenticate(
				request,
				username=username,
				password=password,
			)
			if user:
				login(request, user)
				# Apply session timeout from app settings
				app_settings = AppSettings.load()
				request.session.set_expiry(app_settings.session_timeout)
				account = getattr(user, "account", None)
				target = request_next or (reverse("dockspace:management") if getattr(account, "is_admin", False) else reverse("dockspace:account_profile"))
				return redirect(target)
			messages.error(request, "Invalid credentials or OTP.")
	else:
		form = AccountLoginForm()
	return render(request, "dockspace/pages-login.html", {"form": form, "next": request_next or next_url_default})


def account_register(request):
	"""
	Initial setup registration - only works when no mail accounts exist.
	Creates the first admin account.
	"""
	# Check if any mail accounts exist
	account_count = MailAccount.objects.count()

	if account_count > 0:
		# Registration is disabled if accounts already exist - silently redirect
		return redirect("dockspace:account_login")

	app_settings = AppSettings.load()
	settings_form = AppSettingsForm(instance=app_settings)

	if request.method == "POST":
		# Get form data
		first_name = request.POST.get("first_name", "").strip()
		last_name = request.POST.get("last_name", "").strip()
		email = request.POST.get("email", "").strip()
		username = request.POST.get("username", "").strip()
		password = request.POST.get("password", "")
		password_confirmation = request.POST.get("password_confirmation", "")
		settings_form = AppSettingsForm(request.POST, instance=app_settings)

		# Validation
		errors = []
		if not first_name:
			errors.append("First name is required.")
		if not last_name:
			errors.append("Last name is required.")
		if not email:
			errors.append("Email is required.")
		if not username:
			errors.append("Username is required.")
		if not password or len(password) < 8:
			errors.append("Password must be at least 8 characters.")
		if password != password_confirmation:
			errors.append("Passwords do not match.")

		# Check for existing username/email (double-check even though we checked count)
		if MailAccount.objects.filter(username=username).exists():
			errors.append("Username already exists.")
		if MailAccount.objects.filter(email=email).exists():
			errors.append("Email already exists.")
		if not settings_form.is_valid():
			messages.error(request, "Please correct the application settings fields below.")

		if errors or not settings_form.is_valid():
			for error in errors:
				messages.error(request, error)
			return render(request, "dockspace/pages-register.html", {
				"first_name": first_name,
				"last_name": last_name,
				"email": email,
				"username": username,
				"settings_form": settings_form,
			})


		settings_form.save()

		# Create the first admin account
		account = MailAccount(
			username=username,
			email=email,
			first_name=first_name,
			last_name=last_name,
			is_admin=True,  # First account is always admin
			is_active=True,
		)
		account.set_password(password)
		account.save()

		messages.success(request, f"Admin account created successfully! Welcome, {first_name}. You can now log in.")
		return redirect("dockspace:account_login")

	return render(request, "dockspace/pages-register.html", {"settings_form": settings_form})


def account_recoverpw(request):
	return render(request, "dockspace/pages-recoverpw.html")


@login_required(login_url="dockspace:account_login")
def account_logout(request):
	logout(request)
	messages.success(request, "You have been logged out.")
	return redirect("dockspace:account_login")


def account_totp(request):
	get_token(request)  # ensure CSRF cookie is set
	account_id = request.session.get("pending_totp_account")
	next_url = request.session.get("pending_totp_next") or reverse("oidc_provider:authorize")
	if not account_id:
		return redirect("dockspace:account_login")
	account = MailAccount.objects.filter(id=account_id, is_active=True).first()
	if not account or not account.totp_secret:
		request.session.pop("pending_totp_account", None)
		request.session.pop("pending_totp_next", None)
		return redirect("dockspace:account_login")

	error = None
	if request.method == "POST":
		token = (request.POST.get("otp_token") or "").strip()
		if token:
			try:
				totp = pyotp.TOTP(account.totp_secret)
				if totp.verify(token, valid_window=1):
					MailAccount.objects.filter(pk=account.pk).update(
						totp_last_counter=account.totp_last_counter + 1,
						totp_verified_at=timezone.now(),
					)

					user = AccountUserBackend().get_user(account.id)
					user.backend = "dockspace.auth_backend.AccountUserWithTOTPBackend"
					login(request, user)
					# Apply session timeout from app settings
					app_settings = AppSettings.load()
					request.session.set_expiry(app_settings.session_timeout)
					request.session["totp_verified_account"] = account.id
					request.session["totp_verified_at"] = timezone.now().isoformat()
					request.session.pop("pending_totp_account", None)
					request.session.pop("pending_totp_next", None)
					return redirect(next_url)
			except Exception:
				pass
		error = "Invalid code. Please try again."

	return render(request, "dockspace/pages-2fa.html", {"error": error})


def _account_from_user(user):
	if not user or not getattr(user, "is_authenticated", False):
		return None
	if hasattr(user, "account"):
		return user.account
	email = getattr(user, "email", "") or ""
	if not email:
		return None
	return MailAccount.objects.filter(email__iexact=email).first()


def _totp_artifacts(account):
	if not account or not account.totp_secret or not account.email:
		return None, None
	try:
		totp = pyotp.TOTP(account.totp_secret)
		issuer = getattr(settings, "OTP_TOTP_ISSUER", "") or None
		uri = totp.provisioning_uri(name=account.email, issuer_name=issuer)
		buffer = io.BytesIO()
		qrcode.make(uri).save(buffer, format="PNG")
		encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
		return uri, f"data:image/png;base64,{encoded}"
	except Exception:
		return None, None


@login_required(login_url="dockspace:account_login")
def account_profile(request, account_id=None):
	current_user_account = _account_from_user(request.user)
	if current_user_account is None:
		messages.error(request, "No mail account is linked to this user.")
		return redirect("account_login")

	# Determine if admin is viewing another user's profile
	is_admin_viewing_other = False
	if account_id is not None:
		# Someone is trying to view another account via account_id parameter
		if not getattr(current_user_account, "is_admin", False):
			# Non-admin trying to view another profile - redirect to their own
			messages.error(request, "You do not have permission to view other accounts.")
			return redirect("dockspace:account_profile")

		# Admin viewing another account
		account = MailAccount.objects.filter(id=account_id).first()
		if account is None:
			messages.error(request, "Account not found.")
			return redirect("dockspace:management")

		# Prevent viewing own profile through admin URL (redirect to normal profile)
		if account.id == current_user_account.id:
			return redirect("dockspace:account_profile")

		is_admin_viewing_other = True
	else:
		# User viewing their own profile
		account = current_user_account

	profile_form = MailAccountProfileForm(instance=account)
	totp_form = TOTPVerifyForm()

	if request.method == "POST":
		action = request.POST.get("action")
		if action == "profile":
			profile_form = MailAccountProfileForm(request.POST, request.FILES, instance=account)
			if profile_form.is_valid():
				profile_form.save()
				messages.success(request, f"Profile updated for {account.email}." if is_admin_viewing_other else "Profile updated.")
				if is_admin_viewing_other:
					return redirect("dockspace:account_profile_admin", account_id=account.id)
				return redirect("dockspace:account_profile")
			messages.error(request, "Please fix the errors below.")
		elif action == "totp_generate":
			# Only allow TOTP management for own account
			if is_admin_viewing_other:
				messages.error(request, "You cannot manage TOTP for other accounts.")
				return redirect("dockspace:account_profile_admin", account_id=account.id)
			MailAccount.objects.filter(pk=account.pk).update(
				totp_secret=pyotp.random_base32(),
				totp_verified_at=None,
				totp_last_counter=0,
			)
			account.refresh_from_db(fields=["totp_secret", "totp_verified_at", "totp_last_counter"])
			messages.success(request, "New authenticator secret generated. Scan the code and confirm below.")
			return redirect("dockspace:account_profile")
		elif action == "totp_verify":
			# Only allow TOTP management for own account
			if is_admin_viewing_other:
				messages.error(request, "You cannot manage TOTP for other accounts.")
				return redirect("dockspace:account_profile_admin", account_id=account.id)
			totp_form = TOTPVerifyForm(request.POST)
			if totp_form.is_valid():
				if not account.totp_secret:
					totp_form.add_error(None, "Generate a TOTP secret first.")
				else:
					totp = pyotp.TOTP(account.totp_secret)
					if totp.verify(totp_form.cleaned_data["token"], valid_window=1):
						now = timezone.now()
						MailAccount.objects.filter(pk=account.pk).update(
							totp_verified_at=now,
							totp_last_counter=0,
						)
						account.refresh_from_db(fields=["totp_verified_at", "totp_last_counter"])
						request.session["totp_verified_account"] = account.id
						request.session["totp_verified_at"] = now.isoformat()
						messages.success(request, "Authenticator code verified.")
						return redirect("dockspace:account_profile")
					totp_form.add_error("token", "That code did not match. Try again.")
			else:
				messages.error(request, "Enter the 6-digit code from your authenticator app.")
		elif action == "totp_disable":
			# Only allow TOTP management for own account
			if is_admin_viewing_other:
				messages.error(request, "You cannot manage TOTP for other accounts.")
				return redirect("dockspace:account_profile_admin", account_id=account.id)
			MailAccount.objects.filter(pk=account.pk).update(
				totp_secret="",
				totp_verified_at=None,
				totp_last_counter=0,
			)
			account.refresh_from_db(fields=["totp_secret", "totp_verified_at", "totp_last_counter"])
			messages.success(request, "Two-factor authentication disabled.")
			return redirect("dockspace:account_profile")
		elif action == "reset_password":
			# Password reset logic
			new_password = request.POST.get("new_password", "").strip()
			confirm_password = request.POST.get("confirm_password", "").strip()

			# Validation
			if not new_password or len(new_password) < 8:
				messages.error(request, "Password must be at least 8 characters.")
			elif new_password != confirm_password:
				messages.error(request, "Passwords do not match.")
			else:
				# Check permissions
				if is_admin_viewing_other:
					# Admin resetting another user's password
					# Cannot reset password of another admin
					if getattr(account, "is_admin", False):
						messages.error(request, "You cannot reset the password of another administrator.")
						return redirect("dockspace:account_profile_admin", account_id=account.id)

					account.set_password(new_password)
					account.save()

					# Invalidate all sessions for this user
					from django.contrib.sessions.models import Session

					# Get all active sessions
					for session in Session.objects.filter(expire_date__gte=timezone.now()):
						session_data = session.get_decoded()
						# Check if this session belongs to the user whose password was changed
						if session_data.get('_auth_user_id') == str(account.id):
							session.delete()

					messages.success(request, f"Password reset successfully for {account.email}. User has been logged out of all sessions.")
					return redirect("dockspace:account_profile_admin", account_id=account.id)
				else:
					# User resetting their own password
					account.set_password(new_password)
					account.save()
					messages.success(request, "Password reset successfully. Please log in again with your new password.")
					# Log them out since password changed
					logout(request)
					return redirect("dockspace:account_login")


	provisioning_uri, totp_qr = _totp_artifacts(account)
	context = {
		"account": account,
		"profile_form": profile_form,
		"totp_form": totp_form,
		"totp_provisioning_uri": provisioning_uri,
		"totp_qr": totp_qr,
		"aliases": account.mail_aliases.all().order_by("alias"),
		"groups": account.mail_groups.all().order_by("name"),
		"quota": getattr(account, "mail_quota", None),
		"is_admin_viewing_other": is_admin_viewing_other,
		"current_user_is_admin": getattr(current_user_account, "is_admin", False),
	}
	return render(request, "dockspace/pages-profile.html", context)


@login_required(login_url="dockspace:account_login")
def management_dashboard(request):
	account = _account_from_user(request.user)
	if not account or not getattr(account, "is_admin", False):
		messages.error(request, "You must be an admin to view the management dashboard.")
		return redirect("dockspace:account_profile")

	# Load app settings
	app_settings = AppSettings.load()
	settings_form = AppSettingsForm(instance=app_settings)

	accounts = (
		MailAccount.objects.all()
		.select_related("mail_quota")
		.prefetch_related("mail_aliases", "mail_groups")
		.order_by("email")
	)
	admin_count = MailAccount.objects.filter(is_admin=True).count()
	recent_updated = accounts.order_by("-updated_at")[:5]
	recent_created = accounts.order_by("-created_at")[:5]
	groups = MailGroup.objects.all().order_by("name")
	group_form = MailGroupForm()
	alias_form = MailAliasForm()
	quota_form = MailQuotaForm()
	account_create_form = MailAccountCreateForm()
	client_form = OIDCClientCreateForm() if OIDCClientCreateForm else None
	client_groups_form = ClientGroupsForm()

	def _find_client(identifier):
		"""Resolve a Client by string client_id or integer PK."""
		if not Client or not identifier:
			return None
		# Prefer matching by client_id (e.g., az8l5404...)
		obj = Client.objects.filter(client_id=identifier).first()
		if obj:
			return obj
		try:
			return Client.objects.filter(pk=int(identifier)).first()
		except (TypeError, ValueError):
			return None

	if request.method == "POST":
		action = request.POST.get("action")
		target_account = None
		account_id = request.POST.get("account_id")
		if account_id:
			target_account = MailAccount.objects.filter(id=account_id).first()

		if action == "update_settings":
			settings_form = AppSettingsForm(request.POST, instance=app_settings)
			if settings_form.is_valid():
				settings_form.save()
				# Apply session timeout to current request
				request.session.set_expiry(app_settings.session_timeout)
				messages.success(request, "Application settings updated successfully.")
				return redirect("dockspace:management")
			messages.error(request, "Could not update settings. Check the form for errors.")
		elif action == "create_account":
			account_create_form = MailAccountCreateForm(request.POST)
			if account_create_form.is_valid():
				try:
					new_account = account_create_form.save()
					messages.success(request, f"Account created for {new_account.email}.")
					return redirect("dockspace:management")
				except Exception as exc:
					messages.error(request, f"Could not create account: {exc}")
			else:
				messages.error(request, "Could not create account. Check the form for errors.")
		elif action == "update_quota" and target_account:
			try:
				quota = target_account.mail_quota
			except MailQuota.DoesNotExist:
				quota = MailQuota(user=target_account)
			# Ensure user is set for validation
			quota.user = target_account
			form = MailQuotaForm(request.POST, instance=quota)
			if form.is_valid():
				obj = form.save(commit=False)
				obj.user = target_account
				obj.save()
				messages.success(request, f"Updated quota for {target_account.email}.")
				return redirect("dockspace:management")
			messages.error(request, "Could not update quota. Check the values and try again.")
		elif action == "set_admin" and target_account:
			desired_admin = request.POST.get("is_admin") == "on"
			if not desired_admin:
				if target_account.id == account.id:
					messages.error(request, "You cannot remove your own admin access from the management page.")
					return redirect("dockspace:management")
				current_admins = MailAccount.objects.filter(is_admin=True).count()
				if current_admins <= 1:
					messages.error(request, "At least one admin account is required.")
					return redirect("dockspace:management")
			MailAccount.objects.filter(pk=target_account.pk).update(is_admin=desired_admin)
			if target_account.user:
				target_account.user.is_staff = desired_admin
				target_account.user.save(update_fields=["is_staff"])
			status = "granted" if desired_admin else "removed"
			messages.success(request, f"Admin access {status} for {target_account.email}.")
			return redirect("dockspace:management")
		elif action == "delete_account" and target_account:
			if target_account.id == account.id:
				messages.error(request, "You cannot delete your own account from the management page.")
				return redirect("dockspace:management")
			if target_account.is_admin:
				messages.error(request, "Admin accounts cannot be deleted from the management page.")
				return redirect("dockspace:management")
			target_account.delete()
			messages.success(request, f"Deleted account {target_account.email}.")
			return redirect("dockspace:management")
		elif action == "add_alias" and target_account:
			form = MailAliasForm(request.POST)
			if form.is_valid():
				alias = form.save(commit=False)
				alias.user = target_account
				alias.save()
				messages.success(request, f"Alias added to {target_account.email}.")
				return redirect("dockspace:management")
			messages.error(request, "Could not add alias. Check for duplicates or invalid email.")
		elif action == "remove_alias":
			alias_id = request.POST.get("alias_id")
			alias = MailAlias.objects.filter(id=alias_id).first()
			if alias:
				alias.delete()
				messages.success(request, "Alias removed.")
				return redirect("dockspace:management")
			messages.error(request, "Alias not found.")
		elif action == "update_aliases" and target_account:
			remove_ids = request.POST.getlist("remove_aliases")
			if remove_ids:
				MailAlias.objects.filter(id__in=remove_ids, user=target_account).delete()
			new_alias = (request.POST.get("new_alias") or "").strip()
			if new_alias:
				alias_obj = MailAlias(user=target_account, alias=new_alias)
				try:
					alias_obj.full_clean()
					alias_obj.save()
					messages.success(request, f"Alias changes saved for {target_account.email}.")
				except Exception as exc:
					messages.error(request, f"Could not add alias: {exc}")
					return redirect("dockspace:management")
			else:
				messages.success(request, f"Alias changes saved for {target_account.email}.")
			return redirect("dockspace:management")
		elif action == "update_groups" and target_account:
			form = AccountGroupsForm(request.POST)
			form.fields["groups"].queryset = groups
			if form.is_valid():
				target_account.mail_groups.set(form.cleaned_data["groups"])
				messages.success(request, f"Updated groups for {target_account.email}.")
				return redirect("dockspace:management")
			messages.error(request, "Could not update groups. Check the values and try again.")
		elif action == "create_group":
			group_form = MailGroupForm(request.POST)
			if group_form.is_valid():
				group_form.save()
				messages.success(request, "Group created.")
				return redirect("dockspace:management")
			messages.error(request, "Could not create group.")
		elif action == "update_group":
			group_id = request.POST.get("group_id")
			group = MailGroup.objects.filter(id=group_id).first()
			if group:
				form = MailGroupForm(request.POST, instance=group)
				if form.is_valid():
					form.save()
					messages.success(request, "Group updated.")
					return redirect("dockspace:management")
				messages.error(request, "Could not update group. Check the name.")
			else:
				messages.error(request, "Group not found.")
		elif action == "delete_group":
			group_id = request.POST.get("group_id")
			group = MailGroup.objects.filter(id=group_id).first()
			if group:
				group.delete()
				messages.success(request, "Group deleted.")
				return redirect("dockspace:management")
			messages.error(request, "Group not found.")
		elif action == "create_client" and Client and OIDCClientCreateForm:
			client_form = OIDCClientCreateForm(request.POST)
			if client_form.is_valid():
				client = client_form.save(commit=False)
				# Normalize redirect URIs to newline-separated values if entered as multiline text.
				raw = client_form.cleaned_data.get("redirect_uris") or ""
				uris = [line.strip() for line in raw.splitlines() if line.strip()]
				client.redirect_uris = uris
				scope_raw = (client_form.cleaned_data.get("scope") or "").strip()
				if scope_raw:
					client.scope = scope_raw.split()
				client.save()
				client.response_types.set(client_form.cleaned_data.get("response_types"))
				messages.success(request, "OIDC client created.")
				return redirect("dockspace:management")
			messages.error(request, "Could not create OIDC client. Check required fields.")
		elif action == "update_client" and Client and OIDCClientCreateForm:
			client_id = request.POST.get("client_id")
			client_obj = _find_client(client_id)
			if client_obj:
				form = OIDCClientCreateForm(request.POST, instance=client_obj)
				if form.is_valid():
					client = form.save(commit=False)
					raw = form.cleaned_data.get("redirect_uris") or ""
					client.redirect_uris = [line.strip() for line in raw.splitlines() if line.strip()]
					scope_raw = (form.cleaned_data.get("scope") or "").strip()
					if scope_raw:
						client.scope = scope_raw.split()
					else:
						client.scope = []
					client.save()
					client.response_types.set(form.cleaned_data.get("response_types"))
					messages.success(request, f"Updated client {client.name or client.client_id}.")
					return redirect("dockspace:management")
				messages.error(request, "Could not update client. Check required fields.")
			else:
				messages.error(request, "Client not found.")
		elif action == "delete_client" and Client:
			client_id = request.POST.get("client_id")
			client_obj = _find_client(client_id)
			if client_obj:
				client_obj.delete()
				messages.success(request, "Client deleted.")
				return redirect("dockspace:management")
			messages.error(request, "Client not found.")
		elif action == "update_client_groups" and Client and ClientAccess:
			client_id = request.POST.get("client_id")
			client_obj = _find_client(client_id)
			if client_obj:
				form = ClientGroupsForm(request.POST)
				form.fields["groups"].queryset = groups
				if form.is_valid():
					access, _ = ClientAccess.objects.get_or_create(client=client_obj)
					access.groups.set(form.cleaned_data["groups"])
					access.require_2fa = form.cleaned_data["require_2fa"]
					access.save()
					messages.success(request, f"Updated access settings for {client_obj.name or client_obj.client_id}.")
					return redirect("dockspace:management")
				messages.error(request, "Could not update client settings.")
			else:
				messages.error(request, "Client not found.")
		elif action == "regenerate_rsa_key":
			try:
				from oidc_provider.models import RSAKey
				from oidc_provider.lib.utils.common import get_rsa_key
				# Delete all existing keys
				RSAKey.objects.all().delete()
				# Generate new key
				get_rsa_key()
				messages.success(request, "RSA key regenerated successfully.")
			except Exception as exc:
				messages.error(request, f"Could not regenerate RSA key: {exc}")
			return redirect("dockspace:management")

	clients = Client.objects.all().order_by("-date_created") if Client else []
	if clients:
		for client in clients:
			client.access = ClientAccess.objects.filter(client=client).first()
			if OIDCClientCreateForm:
				initial = {
					"redirect_uris": "\n".join(client.redirect_uris),
					"scope": " ".join(client.scope),
				}
				client.edit_form = OIDCClientCreateForm(instance=client, initial=initial)

	all_aliases = MailAlias.objects.select_related("user").order_by("alias")

	# Check RSA key status and auto-create if missing
	rsa_key_exists = False
	try:
		from oidc_provider.models import RSAKey
		rsa_key_exists = RSAKey.objects.exists()
		# Auto-create RSA key if none exists
		if not rsa_key_exists:
			from oidc_provider.lib.utils.common import get_rsa_key
			get_rsa_key()
			rsa_key_exists = True
	except ImportError:
		pass

	context = {
		"accounts": accounts,
		"recent_updated": recent_updated,
		"recent_created": recent_created,
		"groups": groups,
		"group_form": group_form,
		"alias_form": alias_form,
		"quota_form": quota_form,
		"account_create_form": account_create_form,
		"client_form": client_form,
		"clients": clients,
		"client_groups_form": client_groups_form,
		"Client": Client,
		"all_aliases": all_aliases,
		"settings_form": settings_form,
		"app_settings": app_settings,
		"rsa_key_exists": rsa_key_exists,
		"admin_count": admin_count,
		"current_account": account,
	}
	return render(request, "dockspace/crm-management.html", context)


def root_redirect(request):
	"""Redirect root path to login page."""
	if not MailAccount.objects.exists():
		return redirect("dockspace:account_register")
	return redirect("dockspace:account_login")


def page_not_found_view(request, exception=None):
	return render(request, "dockspace/pages-404.html", status=404)


def _build_profile_url(request):
	"""Return absolute URL to the profile page using AppSettings.domain_url when available."""
	app_settings = AppSettings.objects.first()
	domain = getattr(app_settings, "domain_url", None) or request.get_host()
	normalized_domain = (domain or "").rstrip("/")
	if normalized_domain.startswith("http://") or normalized_domain.startswith("https://"):
		base = normalized_domain
	else:
		base = f"{request.scheme}://{normalized_domain}"
	return f"{base}/profile"


def page_2fa_required(request):
	"""Display 2FA required page with link to profile."""
	profile_url = _build_profile_url(request)
	client_name = request.GET.get('client', None)

	context = {
		'profile_url': profile_url,
		'client_name': client_name,
	}
	return render(request, "dockspace/pages-2fa-required.html", context)


def page_access_denied(request):
	"""Render access denied page for OIDC clients when the user lacks required groups."""
	profile_url = _build_profile_url(request)
	context_data = request.session.pop("access_denied_context", {}) or {}

	context = {
		"profile_url": profile_url,
		"client_name": context_data.get("client_name"),
		"required_groups": context_data.get("required_groups") or [],
		"user_groups": context_data.get("user_groups") or [],
	}
	return render(request, "dockspace/pages-access-denied.html", context, status=403)


@login_required(login_url="dockspace:account_login")
def protected_media(request, path):
	"""Serve media files only to authenticated users."""
	import os
	from django.http import FileResponse, Http404

	media_path = os.path.join(settings.MEDIA_ROOT, path)

	# Security: prevent path traversal attacks
	media_path = os.path.abspath(media_path)
	if not media_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
		raise Http404("Invalid file path")

	if not os.path.exists(media_path) or not os.path.isfile(media_path):
		raise Http404("File not found")

	return FileResponse(open(media_path, 'rb'))
