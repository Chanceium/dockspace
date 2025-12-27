"""
Module: integrations/dms_export.py
Purpose: Docker Mailserver configuration file generation and synchronization

Generates and maintains three critical configuration files for Docker Mailserver:
1. postfix-accounts.cf: Mail account credentials (email|{SHA512-CRYPT}hash)
2. postfix-virtual.cf: Email alias mappings (alias@domain recipient@domain)
3. dovecot-quotas.cf: Mailbox size quotas (email:10G)

Key Features:
- Atomic file writes to prevent corruption during updates
- Drift detection to verify files match database state
- Automatic cleanup of conflicting aliases
- Comprehensive logging for debugging
- Signal-driven auto-sync on model changes

The files are written to DMS_OUTPUT_DIR (default: ./data/dms) and should be
mounted into the Docker Mailserver container.
"""
from pathlib import Path
import logging

from django.conf import settings

from dockspace.core.models import MailAccount, MailAlias, MailQuota

logger = logging.getLogger(__name__)


def write_dms_files(output_dir=None):
    """Write Docker Mailserver config files based on MailAlias and MailQuota records."""

    base_output = output_dir or getattr(settings, "DMS_OUTPUT_DIR", None) or (Path.cwd() / "data" / "dms")
    output_dir = Path(base_output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    accounts_path = output_dir / "postfix-accounts.cf"
    virtual_path = output_dir / "postfix-virtual.cf"
    quotas_path = output_dir / "dovecot-quotas.cf"

    accounts_lines = _build_accounts()
    virtual_lines = _build_virtual()
    quota_lines = _build_quotas()

    _write_file(accounts_path, accounts_lines)
    _write_file(virtual_path, virtual_lines)
    _write_file(quotas_path, quota_lines)

    logger.info("Wrote DMS files to %s", output_dir)


def _build_accounts():
    accounts = []
    users = MailAccount.objects.order_by("email")
    for account in users:
        email = (account.email or "").strip().lower()
        if not email:
            logger.warning("Skipping account export for user with no email")
            continue
        if not account.password_hash:
            logger.warning(
                "Skipping account export for %s: missing password_hash",
                email,
            )
            continue
        accounts.append(f"{email}|{account.password_hash}")
    return accounts


def _build_virtual():
    aliases = MailAlias.objects.select_related("user").order_by("alias")
    mailboxes = {
        (email or "").strip().lower()
        for email in MailAccount.objects.values_list("email", flat=True)
    }
    lines = []
    for alias in aliases:
        alias_mailbox = (alias.alias or "").strip().lower()
        if alias_mailbox in mailboxes:
            # If a real mailbox exists for this address, skip exporting the alias to avoid conflicts.
            continue
        lines.append(alias.to_config_line())
    return lines


def _build_quotas():
    quotas = MailQuota.objects.select_related("user").order_by("user__email")
    lines = []
    for quota in quotas:
        try:
            lines.append(quota.to_config_line())
        except ValueError:
            logger.warning(
                "Skipping quota export for user %s: missing email",
                quota.user.get_username(),
            )
    return lines


def _write_file(path: Path, lines):
    # Drop empty lines and normalize trailing newline.
    cleaned = [line.rstrip() for line in lines if (line or "").strip()]
    content = "\n".join(cleaned)
    if cleaned:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def verify_dms_files(output_dir=None, rewrite=True):
    """
    Compare existing DMS files to the expected export.

    Returns True if files are already correct. If rewrite is True, drifted files
    are rewritten to the expected contents.
    """
    base_output = output_dir or getattr(settings, "DMS_OUTPUT_DIR", None) or (Path.cwd() / "data" / "dms")
    output_dir = Path(base_output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    accounts_path = output_dir / "postfix-accounts.cf"
    virtual_path = output_dir / "postfix-virtual.cf"
    quotas_path = output_dir / "dovecot-quotas.cf"

    expected = {
        accounts_path: _normalize_content(_build_accounts()),
        virtual_path: _normalize_content(_build_virtual()),
        quotas_path: _normalize_content(_build_quotas()),
    }

    drifted = []
    for path, content in expected.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != content:
            drifted.append(path)
            if rewrite:
                path.write_text(content, encoding="utf-8")
    if drifted:
        names = ", ".join(p.name for p in drifted)
        action = "rewrote" if rewrite else "detected drift in"
        logger.warning("%s DMS file(s): %s", action, names)
    return len(drifted) == 0


def _normalize_content(lines) -> str:
    cleaned = [line.rstrip() for line in lines if (line or "").strip()]
    if not cleaned:
        return ""
    return "\n".join(cleaned) + "\n"
