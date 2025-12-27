from pathlib import Path

from django.core.management.base import BaseCommand

from dockspace.integrations.dms_export import verify_dms_files


class Command(BaseCommand):
    help = "Check Docker Mailserver config files for drift; rewrites by default."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Directory containing postfix-accounts.cf, postfix-virtual.cf, dovecot-quotas.cf (defaults to DMS_OUTPUT_DIR).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Detect drift without rewriting files.",
        )

    def handle(self, *args, **options):
        output_dir = options["output_dir"]
        if output_dir:
            output_dir = Path(output_dir).expanduser().resolve()

        is_clean = verify_dms_files(output_dir=output_dir, rewrite=not options["dry_run"])
        if is_clean:
            self.stdout.write(self.style.SUCCESS("DMS files are up to date."))
        else:
            if options["dry_run"]:
                self.stdout.write(self.style.WARNING("Drift detected (dry run, no rewrites)."))
            else:
                self.stdout.write(self.style.WARNING("Drift detected and rewritten."))
