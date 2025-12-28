"""
Module: management/commands/export_dms_files.py
Purpose: Django management command to export Docker Mailserver configuration files

Usage:
    python manage.py export_dms_files [--output-dir PATH]

Generates postfix-accounts.cf, postfix-virtual.cf, and dovecot-quotas.cf files
based on current database state. These files should be mounted into the Docker
Mailserver container for mail account, alias, and quota configuration.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from dockspace.integrations.dms_export import write_dms_files


class Command(BaseCommand):
    help = "Write Docker Mailserver config files (postfix-virtual.cf, dovecot-quotas.cf, postfix-accounts.cf placeholder)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=getattr(settings, "DMS_OUTPUT_DIR", None) or (Path.cwd() / "data" / "dms"),
            help="Destination directory for generated DMS files.",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"]).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        write_dms_files(output_dir)

        accounts_path = output_dir / "postfix-accounts.cf"
        virtual_path = output_dir / "postfix-virtual.cf"
        quotas_path = output_dir / "dovecot-quotas.cf"
        self.stdout.write(self.style.SUCCESS(f"Wrote {accounts_path}"))
        self.stdout.write(self.style.SUCCESS(f"Wrote {virtual_path}"))
        self.stdout.write(self.style.SUCCESS(f"Wrote {quotas_path}"))
