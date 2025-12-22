from django.apps import AppConfig


class DockspaceConfig(AppConfig):
    # Keep label/access DB tables stable while module name changes.
    name = "dockspace"
    label = "access"
    verbose_name = "Dockspace"

    def ready(self):
        # Import signal handlers to keep DMS config files in sync with model changes.
        from . import signals  # noqa: F401
