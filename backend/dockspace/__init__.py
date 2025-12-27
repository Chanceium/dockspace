"""
Dockspace - Mail server management with OIDC authentication.
"""
# Don't import models at module level to avoid AppRegistryNotReady errors
# Models can be imported directly from dockspace.core.models when needed

default_app_config = 'dockspace.apps.DockspaceConfig'
