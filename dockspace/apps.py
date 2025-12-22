from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class DockspaceConfig(AppConfig):
    name = "dockspace"
    label = "dockspace"
    verbose_name = "Dockspace"

    def ready(self):
        # Import signal handlers to keep DMS config files in sync with model changes.
        from . import signals  # noqa: F401
