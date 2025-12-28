"""
Security module for Dockspace.
Contains authentication backends, password validators, and security middleware.
"""
from .auth_backend import AccountUserBackend, AccountUserWithTOTPBackend
from .validators import PasswordComplexityValidator
from .middleware import DomainSettingsMiddleware, SecurityHeadersMiddleware

__all__ = [
    'AccountUserBackend',
    'AccountUserWithTOTPBackend',
    'PasswordComplexityValidator',
    'DomainSettingsMiddleware',
    'SecurityHeadersMiddleware',
]
