"""
Session tracking utility for monitoring user login activity.
"""
import re
import logging
import requests
from django.contrib.sessions.models import Session
from dockspace.core.models import UserSession, MailAccount

logger = logging.getLogger(__name__)


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract browser and device information.
    Returns a dict with 'browser' and 'device' keys.
    """
    ua = user_agent_string.lower()

    # Detect browser
    browser = "Unknown Browser"
    if 'edg' in ua:
        browser = "Edge"
    elif 'chrome' in ua:
        browser = "Chrome"
    elif 'firefox' in ua:
        browser = "Firefox"
    elif 'safari' in ua and 'chrome' not in ua:
        browser = "Safari"
    elif 'opera' in ua or 'opr' in ua:
        browser = "Opera"

    # Detect OS
    os_name = "Unknown OS"
    if 'windows' in ua:
        if 'windows nt 10' in ua:
            os_name = "Windows 10/11"
        elif 'windows nt 6.3' in ua:
            os_name = "Windows 8.1"
        elif 'windows nt 6.2' in ua:
            os_name = "Windows 8"
        elif 'windows nt 6.1' in ua:
            os_name = "Windows 7"
        else:
            os_name = "Windows"
    elif 'mac os x' in ua or 'macos' in ua:
        os_name = "macOS"
    elif 'linux' in ua:
        os_name = "Linux"
    elif 'android' in ua:
        os_name = "Android"
    elif 'iphone' in ua or 'ipad' in ua or 'ipod' in ua:
        os_name = "iOS"

    browser_full = f"{browser} on {os_name}"

    # Detect device type
    device = "Desktop Computer"
    if 'iphone' in ua:
        device = "iPhone"
    elif 'ipad' in ua:
        device = "iPad"
    elif 'android' in ua:
        if 'mobile' in ua:
            device = "Android Phone"
        else:
            device = "Android Tablet"
    elif 'mobile' in ua:
        device = "Mobile Device"

    return {
        'browser': browser_full,
        'device': device,
    }


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Handles proxies and load balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_location_from_ip(ip_address):
    """
    Get location information from IP address using a free geolocation API.
    Returns a location string like "San Francisco, US" or "Unknown Location".

    Args:
        ip_address: IP address string

    Returns:
        str: Location string
    """
    # Skip private/local IPs
    if ip_address in ['127.0.0.1', 'localhost', '0.0.0.0', '::1']:
        return 'Local'

    # Check if it's a private IP range
    if ip_address.startswith(('10.', '172.16.', '172.17.', '172.18.', '172.19.',
                             '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
                             '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
                             '172.30.', '172.31.', '192.168.')):
        return 'Private Network'

    try:
        # Use ip-api.com free tier (no auth required, 45 requests/minute)
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            params={'fields': 'status,city,country'},
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city', '')
                country = data.get('country', '')

                if city and country:
                    return f"{city}, {country}"
                elif country:
                    return country

    except requests.RequestException as e:
        logger.warning(f"Failed to get location for IP {ip_address}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting location for IP {ip_address}: {e}")

    return 'Unknown Location'


def create_or_update_session(request, mail_account):
    """
    Create or update a UserSession record for the current login.

    Args:
        request: Django HttpRequest object
        mail_account: MailAccount instance

    Returns:
        UserSession instance
    """
    session_key = request.session.session_key

    # Ensure session key exists
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Get client info
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    parsed_ua = parse_user_agent(user_agent)

    # Get location from IP address
    location = get_location_from_ip(ip_address)

    # Try to get existing session or create new one
    session, created = UserSession.objects.get_or_create(
        session_key=session_key,
        defaults={
            'account': mail_account,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'browser': parsed_ua['browser'],
            'device': parsed_ua['device'],
            'location': location,
            'is_active': True,
        }
    )

    # If session already exists, update it
    if not created:
        session.account = mail_account
        session.ip_address = ip_address
        session.user_agent = user_agent
        session.browser = parsed_ua['browser']
        session.device = parsed_ua['device']
        session.location = location
        session.is_active = True
        session.save()

    # Mark old sessions for this account as potentially inactive
    # (keep last 10 sessions active, mark older ones as inactive)
    active_sessions = UserSession.objects.filter(
        account=mail_account,
        is_active=True
    ).order_by('-last_activity')[:10]

    active_session_ids = list(active_sessions.values_list('id', flat=True))
    UserSession.objects.filter(
        account=mail_account,
        is_active=True
    ).exclude(id__in=active_session_ids).update(is_active=False)

    return session


def mark_session_inactive(session_key):
    """
    Mark a session as inactive when the user logs out.

    Args:
        session_key: Django session key
    """
    UserSession.objects.filter(session_key=session_key).update(is_active=False)
