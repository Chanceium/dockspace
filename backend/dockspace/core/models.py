"""
Module: core/models.py
Purpose: Core database models for Dockspace application

Defines the primary database models for mail server management and OIDC authentication:

Key Models:
- AppSettings: Singleton model for global application configuration (SMTP, domain, session timeout)
- MailAccount: Primary user/mail account model with OIDC profile claims and TOTP support
- MailAlias: Email alias to mailbox routing for postfix virtual aliases
- MailQuota: Per-user mailbox size limits for dovecot quotas
- MailGroup: User grouping for access control
- ClientAccess: OIDC client access restrictions (group membership, 2FA requirements)

Each model includes comprehensive validation, custom save logic, and methods for
generating Docker Mailserver configuration files. This file may be split up later if it grows.
"""
import io
import os
import re
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator, EmailValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from oidc_provider.models import Client


def profile_picture_upload_path(instance, filename):
    """
    Generate unique upload path for profile pictures.
    Format: profiles/{uuid}.{extension}
    """
    ext = os.path.splitext(filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    return os.path.join('profiles', unique_filename)


class AppSettings(models.Model):
    """
    Global application settings. Enforces singleton pattern - only one row allowed.
    """

    # Session timeout in seconds (default: 86400 = 24 hours)
    session_timeout = models.PositiveIntegerField(
        default=86400,
        help_text="Maximum session length in seconds (e.g., 86400 = 24 hours)",
    )
    allow_registration = models.BooleanField(
        default=False,
        help_text="Allow self-service registration at /register after setup",
    )

    # Domain URL for OIDC and email links
    domain_url = models.URLField(
        max_length=255,
        default="http://localhost:8000",
        help_text="Base domain URL for the application (e.g., https://example.com)",
    )
    smtp_host = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP server hostname for outbound email (e.g., smtp.example.com)",
    )
    smtp_port = models.PositiveIntegerField(
        default=587,
        help_text="SMTP port (e.g., 587 for STARTTLS, 465 for SSL, 25 for plain)",
    )
    smtp_username = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP username if authentication is required",
    )
    smtp_password = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP password if authentication is required",
    )
    smtp_use_tls = models.BooleanField(
        default=True,
        help_text="Use STARTTLS for SMTP",
    )
    smtp_use_ssl = models.BooleanField(
        default=False,
        help_text="Use SSL for SMTP (typically port 465)",
    )
    smtp_from_email = models.EmailField(
        max_length=255,
        default="noreply@example.com",
        help_text="Default From email for outbound messages (e.g., noreply@example.com)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Application Settings"
        verbose_name_plural = "Application Settings"

    def __str__(self):
        return "Application Settings"

    def save(self, *args, **kwargs):
        # Enforce singleton - only one AppSettings instance allowed
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion
        pass

    @classmethod
    def load(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class MailGroup(models.Model):
    """Grouping for MailAccounts used to gate client access."""

    name = models.CharField(max_length=150, unique=True)
    members = models.ManyToManyField("MailAccount", related_name="mail_groups", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClientAccess(models.Model):
    """
    Optional MailGroup bindings and security settings for an OIDC client.

    - If no row exists for a client, any account may use it.
    - If a row exists with no groups, any account may use it.
    - If groups are attached, accounts must belong to at least one.
    - If require_2fa is True, users must have completed TOTP verification.
    """

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="group_access")
    groups = models.ManyToManyField(MailGroup, blank=True, related_name="oidc_clients")
    require_2fa = models.BooleanField(
        default=False,
        help_text="Require two-factor authentication (TOTP) for this client"
    )

    class Meta:
        verbose_name = "Client access"
        verbose_name_plural = "Client access"

    def __str__(self) -> str:
        return f"Access control for {self.client.name or self.client.client_id}"


class MailAlias(models.Model):
    """Maps an alias address to a MailAccount for postfix-virtual.cf."""

    alias = models.EmailField(unique=True, help_text="Alias address exposed to senders")
    user = models.ForeignKey(
        "MailAccount",
        on_delete=models.CASCADE,
        related_name="mail_aliases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["alias"]
        verbose_name = "Mail alias"
        verbose_name_plural = "Mail aliases"

    def __str__(self) -> str:
        return f"{self.alias} -> {self.recipient_email}" if self.recipient_email else self.alias

    @property
    def recipient_email(self) -> str:
        email = getattr(self.user, "email", "") or None
        return email.lower() if email else None

    def to_config_line(self) -> str:
        """Return the postfix-virtual.cf line for this alias mapping."""
        if not self.recipient_email:
            return f"{self.alias} {self.user.email}"
        return f"{self.alias} {self.recipient_email}"

    def save(self, *args, **kwargs):
        # Normalize alias for consistent uniqueness across databases.
        if self.alias:
            self.alias = self.alias.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.alias:
            EmailValidator(message="Alias must be a valid email address.")(self.alias)
            if MailAccount.objects.filter(email__iexact=self.alias).exists():
                raise ValidationError({"alias": "Alias cannot shadow an existing mailbox address."})


class MailQuota(models.Model):
    """Stores per-user quota for dovecot-quotas.cf."""

    SUFFIX_CHOICES = (
        ("B", "Bytes"),
        ("K", "KiB"),
        ("M", "MiB"),
        ("G", "GiB"),
        ("T", "TiB"),
    )

    user = models.OneToOneField(
        "MailAccount",
        on_delete=models.CASCADE,
        related_name="mail_quota",
    )
    size_value = models.PositiveIntegerField(default=10, help_text="Numeric quota size, e.g. 10 or 512")
    suffix = models.CharField(max_length=1, choices=SUFFIX_CHOICES, default="G")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__email"]
        constraints = [
            models.CheckConstraint(condition=models.Q(size_value__gt=0), name="mailquota_size_value_gt_0"),
        ]

    def __str__(self) -> str:
        return f"{self.user.email}: {self.quota_string}"

    @property
    def mailbox(self) -> str:
        email = (getattr(self.user, "email", "") or "").strip().lower()
        return email

    @property
    def quota_string(self) -> str:
        return f"{self.size_value}{self.suffix}"

    def to_config_line(self) -> str:
        """Return the dovecot-quotas.cf line for this mailbox."""
        mailbox = self.mailbox
        if not mailbox:
            raise ValueError("MailQuota requires user email to render dovecot-quotas line")
        return f"{mailbox}:{self.quota_string}"

    def clean(self):
        super().clean()
        if not (getattr(self.user, "email", "") or "").strip():
            raise ValidationError("User must have an email to assign a mail quota.")
        if self.size_value is None or self.size_value <= 0:
            raise ValidationError({"size_value": "Quota size must be greater than zero."})


class MailAccount(models.Model):
    """Primary identity for mail + OIDC. Stores SHA512-CRYPT password and profile claims."""

    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_DEACTIVATED = 'deactivated'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_DEACTIVATED, 'Deactivated'),
    ]

    sha512_validator = RegexValidator(
        regex=r"^\{SHA512-CRYPT\}.+",
        message="Password hash must include the {SHA512-CRYPT} prefix.",
    )
    locale_validator = RegexValidator(
        regex=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$",
        message="Locale must follow BCP47, e.g. en, en-US, fr-CA.",
    )
    phone_validator = RegexValidator(
        regex=r"^\+?[0-9 .\-()]{6,20}$",
        message="Phone must resemble an E.164 number (e.g. +15551234567).",
    )
    country_validator = RegexValidator(
        regex=r"^[A-Z]{2}$",
        message="Country must be ISO 3166-1 alpha-2 (e.g. US, CA).",
    )
    username_validator = RegexValidator(
        regex=r"^[A-Za-z0-9_.-]{3,150}$",
        message="Username must be 3-150 chars of letters, numbers, ., _, or -.",
    )

    # Link to Django User for OIDC provider compatibility
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='account',
        help_text="Associated Django user for OIDC authentication"
    )
    username = models.CharField(max_length=150, unique=True, validators=[username_validator])
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, help_text="Given name")
    last_name = models.CharField(max_length=150, blank=True, default="", help_text="Family name")
    middle_name = models.CharField(max_length=150, blank=True, default="", help_text="Middle name")
    nickname = models.CharField(max_length=150, blank=True, default="", help_text="Nickname")
    profile = models.URLField(blank=True, help_text="Profile URL")
    password_hash = models.CharField(
        max_length=255,
        validators=[sha512_validator],
        help_text="Value like {SHA512-CRYPT}$6$salt$hash",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text="Account status: active, suspended, or deactivated"
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False, help_text="Marks the account as a Dockspace admin.")

    # Profile / claims
    phone_number = models.CharField(
        max_length=50,
        blank=True,
        validators=[phone_validator],
        help_text="E.164-ish format, e.g. +15551234567",
    )
    phone_number_verified = models.BooleanField(default=False)
    picture = models.ImageField(upload_to=profile_picture_upload_path, blank=True)
    website = models.URLField(blank=True)
    gender = models.CharField(max_length=50, blank=True, help_text="OIDC gender claim (string)")
    birthdate = models.DateField(blank=True, null=True, help_text="YYYY-MM-DD")
    zoneinfo = models.CharField(
        max_length=50,
        blank=True,
        help_text="IANA time zone, e.g. America/New_York",
    )
    locale = models.CharField(
        max_length=50,
        blank=True,
        validators=[locale_validator],
        help_text="BCP47 locale tag, e.g. en-US",
    )
    street_address = models.CharField(max_length=255, blank=True)
    locality = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(
        max_length=2,
        blank=True,
        validators=[country_validator],
        help_text="ISO 3166-1 alpha-2 country code, uppercase",
    )

    # TOTP
    totp_secret = models.CharField(max_length=64, blank=True)
    totp_verified_at = models.DateTimeField(blank=True, null=True)
    totp_last_counter = models.BigIntegerField(default=0)

    # Metadata for storing preferences and other JSON data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional account data (notification preferences, etc.)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["email"]
        constraints = [
            models.UniqueConstraint(Lower("username"), name="mailaccount_username_ci_unique"),
            models.UniqueConstraint(Lower("email"), name="mailaccount_email_ci_unique"),
        ]

    def __str__(self) -> str:
        return (self.email or "").lower()

    @property
    def mailbox(self) -> str:
        return (self.email or "").strip().lower()

    def set_password(self, raw_password: str):
        """Set the SHA512-CRYPT hash from a raw password."""
        import crypt

        if not raw_password:
            raise ValueError("raw_password is required")
        hashed = crypt.crypt(raw_password, crypt.mksalt(crypt.METHOD_SHA512))
        if not hashed.startswith("{SHA512-CRYPT}"):
            hashed = f"{{SHA512-CRYPT}}{hashed}"
        self.password_hash = hashed

    def to_config_line(self) -> str:
        mailbox = self.mailbox
        if not mailbox:
            raise ValueError("MailAccount requires email to render postfix-accounts line")
        if not self.password_hash:
            raise ValueError("Password hash is empty; set with set_password().")
        return f"{mailbox}|{self.password_hash}"

    def clean(self):
        super().clean()
        self._normalize_identity_fields()
        self._validate_required_identity_fields()

        if self.country:
            self.country = self.country.upper()
        if self.zoneinfo:
            try:
                ZoneInfo(self.zoneinfo)
            except ZoneInfoNotFoundError:
                raise ValidationError({"zoneinfo": "Zoneinfo must be a valid IANA time zone."})

        if self.picture and getattr(self.picture, "name", ""):
            self._validate_picture()

    def _validate_picture(self):
        try:
            from PIL import Image
        except Exception as exc:  # pragma: no cover
            raise ValidationError({"picture": _(f"Image validation failed: {exc}")})

        self.picture.file.seek(0)
        with Image.open(self.picture.file) as img:
            format_ok = img.format in {"JPEG", "PNG", "GIF", "WEBP"}
            if not format_ok:
                raise ValidationError({"picture": "Unsupported image format. Use JPEG, PNG, GIF, or WEBP."})

            width, height = img.size
            if width != height:
                raise ValidationError({"picture": "Image must be square (1:1 aspect ratio)."})

            max_px = 1024
            if width > max_px or height > max_px:
                raise ValidationError({"picture": f"Image too large; max {max_px}x{max_px}px."})

    def _processed_picture_content(self):
        from PIL import Image

        self.picture.file.seek(0)
        with Image.open(self.picture.file) as img:
            img = img.convert("RGBA")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
        return ContentFile(buffer.getvalue())

    def save(self, *args, **kwargs):
        self._normalize_identity_fields()
        self._validate_required_identity_fields()
        old_picture = None
        if self.pk:
            try:
                old_picture = MailAccount.objects.get(pk=self.pk).picture
            except MailAccount.DoesNotExist:
                old_picture = None

        incoming_picture = self.picture if getattr(self.picture, "name", "") else None

        if incoming_picture:
            self._validate_picture()
            content = self._processed_picture_content()
            filename = f"{self.pk or 'temp'}.png"
            self.picture.save(filename, content, save=False)

        super().save(*args, **kwargs)

        # Create or update linked Django User for OIDC compatibility
        if not self.user:
            self.user = User.objects.create(
                username=self.email,
                email=self.email,
                is_staff=False,
                is_superuser=False,
                is_active=self.is_active,
            )
            # Save again to update the user foreign key
            super().save(update_fields=['user'])
        else:
            # Update user fields if they changed
            if self.user.username != self.email or self.user.email != self.email or self.user.is_active != self.is_active:
                self.user.username = self.email
                self.user.email = self.email
                self.user.is_active = self.is_active
                self.user.save()

        # If saved with temp filename before PK existed, rename to PK-based name
        if self.picture and getattr(self.picture, "name", "").startswith("pictures/temp") and self.pk:
            storage = self.picture.storage
            desired = f"pictures/{self.pk}.png"
            if storage.exists(self.picture.name) and self.picture.name != desired:
                with storage.open(self.picture.name, "rb") as fh:
                    storage.save(desired, fh)
                storage.delete(self.picture.name)
                self.picture.name = desired
                super().save()

        if old_picture and old_picture.name and old_picture.name != getattr(self.picture, "name", None):
            storage = old_picture.storage
            if storage.exists(old_picture.name):
                storage.delete(old_picture.name)

    def _normalize_identity_fields(self):
        # Keep identity fields consistent and enforce nickname = username
        username = (self.username or self.email or "").strip()
        self.username = username.lower()
        self.email = (self.email or "").strip().lower()
        self.nickname = self.username

    def _validate_required_identity_fields(self):
        required_fields = {
            "username": self.username,
            "first_name": self.first_name,
            "email": self.email,
            "password_hash": self.password_hash,
        }
        if getattr(self, "_skip_password_required", False):
            required_fields.pop("password_hash", None)
        errors = {}
        for field, value in required_fields.items():
            if not (value or "").strip():
                errors[field] = "This field is required."
        if errors:
            raise ValidationError(errors)

    def delete(self, using=None, keep_parents=False):
        if self.picture and self.picture.name:
            storage = self.picture.storage
            name = self.picture.name
            super().delete(using=using, keep_parents=keep_parents)
            if storage.exists(name):
                storage.delete(name)
            return
        return super().delete(using=using, keep_parents=keep_parents)


class TOTPDevice(models.Model):
    """
    TOTP device for two-factor authentication.
    Allows users to have multiple named authenticator devices.
    """
    account = models.ForeignKey(
        MailAccount,
        on_delete=models.CASCADE,
        related_name='totp_devices'
    )
    name = models.CharField(
        max_length=100,
        help_text="Device name (e.g., 'iPhone 14', 'Google Authenticator')"
    )
    secret = models.CharField(
        max_length=64,
        help_text="TOTP secret key"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this device was first verified"
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this device was used for authentication"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['account', 'name']]

    def __str__(self):
        return f"{self.account.email} - {self.name}"


class UserSession(models.Model):
    """
    Track user login sessions for security monitoring.
    Records browser, device, location, and activity for each login.
    """
    account = models.ForeignKey(
        MailAccount,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(
        max_length=40,
        help_text="Django session key"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of the client"
    )
    user_agent = models.TextField(
        help_text="User agent string from the browser"
    )
    browser = models.CharField(
        max_length=100,
        blank=True,
        help_text="Parsed browser name (e.g., 'Chrome on Windows')"
    )
    device = models.CharField(
        max_length=100,
        blank=True,
        help_text="Parsed device name"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Approximate location (city, country)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this session is still active"
    )

    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['account', '-last_activity']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        return f"{self.account.email} - {self.browser} ({self.ip_address})"


class AuditLog(models.Model):
    """
    Audit log for tracking all administrative and user actions.
    Records who did what, when, and from where for compliance and security.
    """
    ACTION_TYPES = [
        # Mail Account Actions
        ('account.create', 'Account Created'),
        ('account.update', 'Account Updated'),
        ('account.delete', 'Account Deleted'),
        ('account.suspend', 'Account Suspended'),
        ('account.activate', 'Account Activated'),
        ('account.password_change', 'Password Changed'),

        # Mail Alias Actions
        ('alias.create', 'Alias Created'),
        ('alias.delete', 'Alias Deleted'),

        # Mail Group Actions
        ('group.create', 'Group Created'),
        ('group.update', 'Group Updated'),
        ('group.delete', 'Group Deleted'),
        ('group.member_add', 'Member Added to Group'),
        ('group.member_remove', 'Member Removed from Group'),

        # Mail Quota Actions
        ('quota.create', 'Quota Created'),
        ('quota.update', 'Quota Updated'),
        ('quota.delete', 'Quota Deleted'),

        # OIDC Client Actions
        ('oidc.create', 'OIDC Client Created'),
        ('oidc.update', 'OIDC Client Updated'),
        ('oidc.delete', 'OIDC Client Deleted'),

        # Application Settings Actions
        ('settings.update', 'Application Settings Updated'),
        ('settings.smtp_update', 'SMTP Settings Updated'),

        # Authentication Actions
        ('auth.login', 'User Login'),
        ('auth.logout', 'User Logout'),
        ('auth.login_failed', 'Login Failed'),
        ('auth.2fa_enabled', '2FA Enabled'),
        ('auth.2fa_disabled', '2FA Disabled'),

        # Session Actions
        ('session.created', 'Session Created'),
        ('session.terminated', 'Session Terminated'),
    ]

    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    # Who performed the action
    actor = models.ForeignKey(
        MailAccount,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs_as_actor',
        help_text="The account that performed this action"
    )

    # What action was performed
    action = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )

    # Who/what was affected
    target_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of object affected (e.g., 'MailAccount', 'MailGroup')"
    )
    target_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the affected object"
    )
    target_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable name of the affected object"
    )

    # Additional context
    description = models.TextField(
        blank=True,
        help_text="Human-readable description of what happened"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional structured data about the action (changes, before/after, etc.)"
    )

    # Security context
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which the action was performed"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent of the client that performed the action"
    )

    # Severity and status
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='info',
        help_text="Severity level of this action"
    )

    success = models.BooleanField(
        default=True,
        help_text="Whether the action completed successfully"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this action occurred"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['severity', '-created_at']),
        ]
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'

    def __str__(self):
        actor_email = self.actor.email if self.actor else 'System'
        return f"{actor_email} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def log(cls, action, actor=None, target_type=None, target_id=None, target_name=None,
            description='', metadata=None, ip_address=None, user_agent=None,
            severity='info', success=True):
        """
        Convenience method to create audit log entries.

        Usage:
            AuditLog.log(
                action='account.create',
                actor=request.user.mailaccount,
                target_type='MailAccount',
                target_id=new_account.id,
                target_name=new_account.email,
                description=f"Created new mail account: {new_account.email}",
                metadata={'quota': '5GB', 'is_admin': False},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
        """
        return cls.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            success=success,
        )


class UserMailbox(models.Model):
    """
    User-configured external mailbox for IMAP/SMTP email client.

    Stores connection details for external email accounts (Gmail, Outlook, etc.)
    that users want to access through the Dockspace mail client interface.
    """

    # Owner
    account = models.ForeignKey(
        MailAccount,
        on_delete=models.CASCADE,
        related_name='user_mailboxes',
        help_text="The Dockspace account that owns this mailbox configuration"
    )

    # Mailbox identification
    name = models.CharField(
        max_length=255,
        help_text="Display name for this mailbox (e.g., 'Work Gmail')"
    )
    email = models.EmailField(
        max_length=255,
        help_text="Email address for this mailbox"
    )

    # IMAP settings (incoming mail)
    imap_host = models.CharField(
        max_length=255,
        help_text="IMAP server hostname (e.g., imap.gmail.com)"
    )
    imap_port = models.PositiveIntegerField(
        default=993,
        help_text="IMAP server port (typically 993 for SSL/TLS)"
    )
    imap_security = models.CharField(
        max_length=20,
        choices=[
            ('None', 'None'),
            ('SSL/TLS', 'SSL/TLS'),
            ('STARTTLS', 'STARTTLS'),
        ],
        default='SSL/TLS',
        help_text="IMAP connection security"
    )

    # SMTP settings (outgoing mail)
    smtp_host = models.CharField(
        max_length=255,
        help_text="SMTP server hostname (e.g., smtp.gmail.com)"
    )
    smtp_port = models.PositiveIntegerField(
        default=587,
        help_text="SMTP server port (typically 587 for STARTTLS)"
    )
    smtp_security = models.CharField(
        max_length=20,
        choices=[
            ('None', 'None'),
            ('SSL/TLS', 'SSL/TLS'),
            ('STARTTLS', 'STARTTLS'),
        ],
        default='STARTTLS',
        help_text="SMTP connection security"
    )

    # Authentication
    username = models.CharField(
        max_length=255,
        help_text="Username for authentication (usually the email address)"
    )
    password = models.CharField(
        max_length=500,
        help_text="Password or app-specific password (stored encrypted)"
    )

    # UI settings
    color = models.CharField(
        max_length=20,
        default='primary',
        help_text="Color theme for this mailbox in UI"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this mailbox is currently active/enabled"
    )

    # Connection status
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful connection timestamp"
    )
    has_error = models.BooleanField(
        default=False,
        help_text="Whether the last connection attempt failed"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Last connection error message"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['account', 'name']
        unique_together = ['account', 'email']
        indexes = [
            models.Index(fields=['account', '-created_at']),
            models.Index(fields=['account', 'is_active']),
        ]
        verbose_name = 'User Mailbox'
        verbose_name_plural = 'User Mailboxes'

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.account.email}"

    def get_mail_client(self):
        """
        Create and return a MailClient instance for this mailbox.

        Returns:
            MailClient instance configured for this mailbox
        """
        from dockspace.core.mail_client import MailClient

        return MailClient(
            imap_host=self.imap_host,
            imap_port=self.imap_port,
            imap_security=self.imap_security,
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            smtp_security=self.smtp_security,
            username=self.username,
            password=self.password
        )

    def test_connection(self):
        """
        Test IMAP/SMTP connection and update status.

        Returns:
            Tuple of (success, message)
        """
        try:
            client = self.get_mail_client()
            success, message = client.test_connection()

            if success:
                self.has_error = False
                self.error_message = ''
                self.last_sync = models.functions.Now()
            else:
                self.has_error = True
                self.error_message = message

            self.save()
            return success, message

        except Exception as e:
            self.has_error = True
            self.error_message = str(e)
            self.save()
            return False, str(e)
