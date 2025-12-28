"""
User session API endpoints.
Handles listing and managing user login sessions.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dockspace.core.models import MailAccount, UserSession
from dockspace.api.decorators import json_login_required


@json_login_required
@require_http_methods(["GET"])
def list_sessions(request):
	"""List recent login sessions for the current user."""
	try:
		mail_account = MailAccount.objects.get(user=request.user)
	except MailAccount.DoesNotExist:
		return JsonResponse({
			'success': False,
			'error': 'Account not found'
		}, status=404)

	# Get recent sessions (last 10)
	sessions = UserSession.objects.filter(account=mail_account)[:10]

	session_list = [{
		'id': session.id,
		'browser': session.browser or 'Unknown Browser',
		'device': session.device or 'Unknown Device',
		'location': session.location or 'Unknown Location',
		'ip_address': session.ip_address,
		'last_activity': session.last_activity.isoformat() if session.last_activity else None,
		'created_at': session.created_at.isoformat() if session.created_at else None,
		'is_active': session.is_active,
		'is_current': session.session_key == request.session.session_key,
	} for session in sessions]

	return JsonResponse({
		'success': True,
		'sessions': session_list
	})
