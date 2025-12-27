"""
Core module for Dockspace.
Contains database models and views.
"""
from .models import (
    AppSettings,
    MailAccount,
    MailAlias,
    MailGroup,
    MailQuota,
    ClientAccess,
)
from .views import vue_spa_view, protected_media

__all__ = [
    'AppSettings',
    'MailAccount',
    'MailAlias',
    'MailGroup',
    'MailQuota',
    'ClientAccess',
    'vue_spa_view',
    'protected_media',
]
