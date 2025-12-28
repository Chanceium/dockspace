"""
Custom decorators for API endpoints.
Provides JSON-friendly authentication and authorization decorators.
"""
from functools import wraps
from django.http import JsonResponse


def json_login_required(view_func):
	"""
	Decorator for views that checks if the user is authenticated.
	Returns JSON response instead of redirecting to login page.

	Usage:
		@json_login_required
		@require_http_methods(["GET"])
		def my_view(request):
			...
	"""
	@wraps(view_func)
	def wrapper(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return JsonResponse({
				'success': False,
				'error': 'Authentication required'
			}, status=401)
		return view_func(request, *args, **kwargs)
	return wrapper


def json_admin_required(view_func):
	"""
	Decorator for views that checks if the user is authenticated and is an admin.
	Returns JSON response instead of redirecting to login page.

	Usage:
		@json_admin_required
		@require_http_methods(["POST"])
		def my_admin_view(request):
			...
	"""
	@wraps(view_func)
	def wrapper(request, *args, **kwargs):
		if not request.user.is_authenticated:
			return JsonResponse({
				'success': False,
				'error': 'Authentication required'
			}, status=401)

		# Check if user has an associated MailAccount and is admin
		try:
			from dockspace.core.models import MailAccount
			mail_account = MailAccount.objects.get(user=request.user)
			if not mail_account.is_admin:
				return JsonResponse({
					'success': False,
					'error': 'Admin privileges required'
				}, status=403)
		except MailAccount.DoesNotExist:
			return JsonResponse({
				'success': False,
				'error': 'Account not found'
			}, status=404)

		return view_func(request, *args, **kwargs)
	return wrapper
