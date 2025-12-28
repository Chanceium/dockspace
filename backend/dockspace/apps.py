"""
Module: apps.py
Purpose: Django application configuration for Dockspace

Defines the DockspaceConfig class which configures the Dockspace Django app.
Imports signal handlers on app ready to ensure DMS config files stay synchronized
with model changes.
"""
from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class DockspaceConfig(AppConfig):
    name = "dockspace"
    label = "dockspace"
    verbose_name = "Dockspace"

    def ready(self):
        # Import signal handlers to keep DMS config files in sync with model changes.
        from dockspace.integrations import signals  # noqa: F401
