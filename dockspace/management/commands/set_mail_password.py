import crypt

from django.core.management.base import BaseCommand, CommandError

from dockspace.models import AccountUser, MailAccount
from dockspace.dms_export import write_dms_files


class Command(BaseCommand):
    help = "Set Docker Mailserver (postfix-accounts) password hash for a user and regenerate DMS files."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email of the account user")
        parser.add_argument(
            "--password",
            dest="password",
            help="Raw password to hash with SHA512-CRYPT for DMS",
            required=True,
        )

    def handle(self, *args, **options):
        email_arg = options["email"]
        raw_password = options["password"]
        try:
            user = AccountUser.objects.get(email__iexact=email_arg)
        except AccountUser.DoesNotExist:
            raise CommandError(f"Account user {email_arg} does not exist")

        email = (user.email or "").strip().lower()
        if not email:
            raise CommandError("Account user must have an email to create postfix account entry")

        account, _ = MailAccount.objects.get_or_create(user=user)
        hashed = crypt.crypt(raw_password, crypt.mksalt(crypt.METHOD_SHA512))
        if not hashed.startswith("{SHA512-CRYPT}"):
            hashed = f"{{SHA512-CRYPT}}{hashed}"
        account.password_hash = hashed
        account.save(update_fields=["password_hash"])

        self.stdout.write(self.style.SUCCESS(f"Updated MailAccount for {email}"))

        write_dms_files()
        self.stdout.write(self.style.SUCCESS("Regenerated DMS files."))
