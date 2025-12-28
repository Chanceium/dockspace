"""
Mail client API endpoints.
Handles user mailbox configurations, email fetching, and sending via IMAP/SMTP.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction

from dockspace.api.decorators import json_login_required
from dockspace.core.models import MailAccount, UserMailbox
from dockspace.core.mail_client import MailClientException


@json_login_required
@require_http_methods(["GET"])
def list_mailboxes(request):
    """List all mailboxes for current user."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    mailboxes = UserMailbox.objects.filter(account=mail_account).order_by('-created_at')

    mailbox_list = []
    for mailbox in mailboxes:
        mailbox_list.append({
            'id': mailbox.id,
            'name': mailbox.name,
            'email': mailbox.email,
            'imapHost': mailbox.imap_host,
            'imapPort': mailbox.imap_port,
            'imapSecurity': mailbox.imap_security,
            'smtpHost': mailbox.smtp_host,
            'smtpPort': mailbox.smtp_port,
            'smtpSecurity': mailbox.smtp_security,
            'username': mailbox.username,
            'color': mailbox.color,
            'isActive': mailbox.is_active,
            'hasError': mailbox.has_error,
            'errorMessage': mailbox.error_message,
            'lastSync': mailbox.last_sync.isoformat() if mailbox.last_sync else None,
        })

    return JsonResponse({'success': True, 'mailboxes': mailbox_list})


@json_login_required
@require_http_methods(["POST"])
def create_mailbox(request):
    """Create a new mailbox configuration."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['name', 'email', 'imapHost', 'imapPort', 'smtpHost', 'smtpPort', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)

        # Check if mailbox with this email already exists for this user
        if UserMailbox.objects.filter(account=mail_account, email=data['email']).exists():
            return JsonResponse({
                'success': False,
                'error': 'A mailbox with this email address already exists'
            }, status=400)

        # Create mailbox
        with transaction.atomic():
            mailbox = UserMailbox.objects.create(
                account=mail_account,
                name=data['name'],
                email=data['email'],
                imap_host=data['imapHost'],
                imap_port=data['imapPort'],
                imap_security=data.get('imapSecurity', 'SSL/TLS'),
                smtp_host=data['smtpHost'],
                smtp_port=data['smtpPort'],
                smtp_security=data.get('smtpSecurity', 'STARTTLS'),
                username=data['username'],
                password=data['password'],  # TODO: Encrypt password
                color=data.get('color', 'primary'),
                is_active=data.get('isActive', True),
            )

            # Test connection
            success, message = mailbox.test_connection()

        return JsonResponse({
            'success': True,
            'mailbox': {
                'id': mailbox.id,
                'name': mailbox.name,
                'email': mailbox.email,
                'imapHost': mailbox.imap_host,
                'imapPort': mailbox.imap_port,
                'imapSecurity': mailbox.imap_security,
                'smtpHost': mailbox.smtp_host,
                'smtpPort': mailbox.smtp_port,
                'smtpSecurity': mailbox.smtp_security,
                'username': mailbox.username,
                'color': mailbox.color,
                'isActive': mailbox.is_active,
                'hasError': mailbox.has_error,
                'errorMessage': mailbox.error_message,
                'lastSync': mailbox.last_sync.isoformat() if mailbox.last_sync else None,
            },
            'connectionTest': {
                'success': success,
                'message': message
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["PUT"])
def update_mailbox(request, mailbox_id):
    """Update mailbox configuration."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)

    try:
        data = json.loads(request.body)

        # Update fields
        if 'name' in data:
            mailbox.name = data['name']
        if 'email' in data:
            mailbox.email = data['email']
        if 'imapHost' in data:
            mailbox.imap_host = data['imapHost']
        if 'imapPort' in data:
            mailbox.imap_port = data['imapPort']
        if 'imapSecurity' in data:
            mailbox.imap_security = data['imapSecurity']
        if 'smtpHost' in data:
            mailbox.smtp_host = data['smtpHost']
        if 'smtpPort' in data:
            mailbox.smtp_port = data['smtpPort']
        if 'smtpSecurity' in data:
            mailbox.smtp_security = data['smtpSecurity']
        if 'username' in data:
            mailbox.username = data['username']
        if 'password' in data:
            mailbox.password = data['password']  # TODO: Encrypt password
        if 'color' in data:
            mailbox.color = data['color']
        if 'isActive' in data:
            mailbox.is_active = data['isActive']

        mailbox.save()

        # Test connection if credentials changed
        if any(key in data for key in ['imapHost', 'imapPort', 'smtpHost', 'smtpPort', 'username', 'password']):
            success, message = mailbox.test_connection()
        else:
            success, message = True, "Settings updated"

        return JsonResponse({
            'success': True,
            'mailbox': {
                'id': mailbox.id,
                'name': mailbox.name,
                'email': mailbox.email,
                'imapHost': mailbox.imap_host,
                'imapPort': mailbox.imap_port,
                'imapSecurity': mailbox.imap_security,
                'smtpHost': mailbox.smtp_host,
                'smtpPort': mailbox.smtp_port,
                'smtpSecurity': mailbox.smtp_security,
                'username': mailbox.username,
                'color': mailbox.color,
                'isActive': mailbox.is_active,
                'hasError': mailbox.has_error,
                'errorMessage': mailbox.error_message,
                'lastSync': mailbox.last_sync.isoformat() if mailbox.last_sync else None,
            },
            'connectionTest': {
                'success': success,
                'message': message
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["DELETE"])
def delete_mailbox(request, mailbox_id):
    """Delete a mailbox configuration."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
        mailbox.delete()

        return JsonResponse({
            'success': True,
            'message': 'Mailbox deleted successfully'
        })

    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["POST"])
def test_mailbox_connection(request, mailbox_id):
    """Test IMAP/SMTP connection for a mailbox."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
        success, message = mailbox.test_connection()

        return JsonResponse({
            'success': True,
            'connectionTest': {
                'success': success,
                'message': message
            }
        })

    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["GET"])
def list_folders(request, mailbox_id):
    """List IMAP folders for a mailbox."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
        client = mailbox.get_mail_client()

        folders = client.list_folders()

        return JsonResponse({
            'success': True,
            'folders': folders
        })

    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)
    except MailClientException as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["GET"])
def fetch_emails(request, mailbox_id):
    """Fetch emails from a mailbox folder."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
        client = mailbox.get_mail_client()

        # Get query parameters
        folder = request.GET.get('folder', 'INBOX')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        emails = client.fetch_emails(folder=folder, limit=limit, offset=offset)

        return JsonResponse({
            'success': True,
            'emails': emails,
            'count': len(emails)
        })

    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)
    except MailClientException as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["GET"])
def fetch_email_detail(request, mailbox_id, email_id):
    """Fetch full email details including body and attachments."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
        client = mailbox.get_mail_client()

        folder = request.GET.get('folder', 'INBOX')
        email_detail = client.fetch_email_detail(folder=folder, email_id=email_id)

        return JsonResponse({
            'success': True,
            'email': email_detail
        })

    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)
    except MailClientException as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@json_login_required
@require_http_methods(["POST"])
def send_email(request, mailbox_id):
    """Send an email via SMTP."""
    try:
        mail_account = MailAccount.objects.get(user=request.user)
    except MailAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)

    try:
        mailbox = UserMailbox.objects.get(id=mailbox_id, account=mail_account)
    except UserMailbox.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mailbox not found'}, status=404)

    try:
        data = json.loads(request.body)

        # Validate required fields
        if not data.get('to') or not data.get('subject'):
            return JsonResponse({
                'success': False,
                'error': 'To and subject are required'
            }, status=400)

        client = mailbox.get_mail_client()

        client.send_email(
            to=data['to'],
            subject=data['subject'],
            body=data.get('body', ''),
            cc=data.get('cc'),
            bcc=data.get('bcc'),
            reply_to=data.get('replyTo')
        )

        return JsonResponse({
            'success': True,
            'message': 'Email sent successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except MailClientException as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
