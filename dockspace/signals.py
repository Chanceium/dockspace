import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .dms_export import write_dms_files
from .models import MailAccount, MailAlias, MailQuota

logger = logging.getLogger(__name__)


def _sync_dms_files():
    try:
        write_dms_files()
    except Exception:
        logger.exception("Failed to write DMS files after model change")


def _remove_aliases_for_mailbox(mailbox: str) -> int:
    """Delete aliases that collide with an actual mailbox address."""
    mailbox = (mailbox or "").strip().lower()
    if not mailbox:
        return 0
    deleted, _ = MailAlias.objects.filter(alias__iexact=mailbox).delete()
    if deleted:
        logger.info("Removed %s alias(es) shadowing mailbox %s", deleted, mailbox)
    return deleted


@receiver(post_save, sender=MailAlias)
@receiver(post_delete, sender=MailAlias)
def mail_alias_changed(**kwargs):
    _sync_dms_files()


@receiver(post_save, sender=MailQuota)
@receiver(post_delete, sender=MailQuota)
def mail_quota_changed(**kwargs):
    _sync_dms_files()


@receiver(post_delete, sender=MailAccount)
def mail_account_deleted(**kwargs):
    _sync_dms_files()


@receiver(post_save, sender=MailAccount)
def mail_account_saved(sender, instance, created, **kwargs):
    _remove_aliases_for_mailbox(getattr(instance, "email", ""))
    _sync_dms_files()
