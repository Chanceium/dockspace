"""
Integrations module for Dockspace.
Contains Docker Mail Server export, OIDC hooks, and signal handlers.
"""
from .dms_export import write_dms_files, verify_dms_files
from .hooks import enforce_group_access
from .userinfo import userinfo

__all__ = [
    'write_dms_files',
    'verify_dms_files',
    'enforce_group_access',
    'userinfo',
]
