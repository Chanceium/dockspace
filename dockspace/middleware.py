import logging
from urllib.parse import urlparse

from django.conf import settings

from .models import AppSettings


logger = logging.getLogger(__name__)


def _derive_host_parts(domain_url: str):
	parsed = urlparse(domain_url or "")
	host = parsed.hostname
	port = parsed.port
	scheme = parsed.scheme or "https"
	origin = None
	if host:
		origin = f"{scheme}://{host}"
		if port:
			origin = f"{scheme}://{host}:{port}"
	return host, port, origin


def apply_domain_settings():
	"""Dynamically extend ALLOWED_HOSTS based on AppSettings.domain_url."""
	try:
		app_settings = AppSettings.load()
		host, port, origin = _derive_host_parts(app_settings.domain_url)
		if not host:
			return

		allowed = set(settings.ALLOWED_HOSTS or [])
		allowed.add(host)
		if port:
			allowed.add(f"{host}:{port}")
		settings.ALLOWED_HOSTS = list(allowed)
	except Exception as exc:  # pragma: no cover - defensive to avoid startup failures
		logger.warning("Could not apply domain settings: %s", exc)


def apply_smtp_settings():
	"""Configure Django email settings from AppSettings SMTP values."""
	try:
		app_settings = AppSettings.load()
		if not app_settings.smtp_host:
			return

		settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
		settings.EMAIL_HOST = app_settings.smtp_host
		settings.EMAIL_PORT = app_settings.smtp_port or 587
		settings.EMAIL_HOST_USER = app_settings.smtp_username or ""
		settings.EMAIL_HOST_PASSWORD = app_settings.smtp_password or ""
		settings.EMAIL_USE_TLS = bool(app_settings.smtp_use_tls)
		settings.EMAIL_USE_SSL = bool(app_settings.smtp_use_ssl)
		settings.DEFAULT_FROM_EMAIL = app_settings.smtp_from_email or settings.DEFAULT_FROM_EMAIL
	except Exception as exc:  # pragma: no cover - defensive to avoid startup failures
		logger.warning("Could not apply SMTP settings: %s", exc)


class DomainSettingsMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		apply_domain_settings()
		apply_smtp_settings()

	def __call__(self, request):
		return self.get_response(request)
