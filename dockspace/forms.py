from django import forms

from .models import AppSettings, MailAccount, MailAlias, MailGroup, MailQuota

try:
    from oidc_provider.models import Client
except Exception:  # pragma: no cover - fallback if oidc_provider not installed
    Client = None

from .models import ClientAccess


class AppSettingsForm(forms.ModelForm):
    """Edit global application settings."""

    SECURITY_CHOICES = (
        ("none", "None"),
        ("starttls", "STARTTLS"),
        ("ssl", "SSL/TLS"),
    )

    session_timeout = forms.IntegerField(
        min_value=300,  # Minimum 5 minutes
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "86400"}),
        help_text="Maximum session length in seconds (e.g., 86400 = 24 hours, 3600 = 1 hour)",
    )

    domain_url = forms.URLField(
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com"}),
        help_text="Base domain URL for OIDC and email links (e.g., https://example.com). No trailing slash.",
    )

    smtp_host = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "smtp.example.com"}),
        help_text="SMTP server hostname for outbound email.",
    )

    smtp_port = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "587"}),
        help_text="SMTP port (e.g., 587 for STARTTLS, 465 for SSL).",
    )

    smtp_username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "SMTP username"}),
        help_text="Leave blank if your server does not require authentication.",
    )

    smtp_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "SMTP password"}),
        help_text="Leave blank to keep the existing password.",
    )

    smtp_use_tls = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Enable STARTTLS.",
    )

    smtp_use_ssl = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Use SSL (typically port 465).",
    )

    smtp_from_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "noreply@example.com"}),
        help_text="Address used as the From header for outbound email.",
    )

    smtp_security = forms.ChoiceField(
        required=False,
        choices=SECURITY_CHOICES,
        widget=forms.RadioSelect,
        help_text="Choose encryption for SMTP.",
    )

    class Meta:
        model = AppSettings
        fields = (
            "session_timeout",
            "domain_url",
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email",
            "smtp_security",
        )

    def clean_domain_url(self):
        url = self.cleaned_data.get("domain_url")
        # Remove trailing slash if present
        if url and url.endswith("/"):
            url = url.rstrip("/")
        return url

    def clean_smtp_password(self):
        password = self.cleaned_data.get("smtp_password")
        if not password and self.instance and self.instance.smtp_password:
            # Preserve existing password if none provided
            return self.instance.smtp_password
        return password

    def clean(self):
        cleaned = super().clean()
        security = cleaned.get("smtp_security")
        cleaned["smtp_use_tls"] = security == "starttls"
        cleaned["smtp_use_ssl"] = security == "ssl"
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance") or getattr(self, "instance", None)
        if instance:
            if instance.smtp_use_ssl:
                initial_security = "ssl"
            elif instance.smtp_use_tls:
                initial_security = "starttls"
            else:
                initial_security = "none"
            self.fields["smtp_security"].initial = initial_security


class MailAccountProfileForm(forms.ModelForm):
    """Profile editor for MailAccount owners."""

    birthdate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    class Meta:
        model = MailAccount
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "phone_number",
            "website",
            "profile",
            "gender",
            "birthdate",
            "zoneinfo",
            "locale",
            "street_address",
            "locality",
            "region",
            "postal_code",
            "country",
            "picture",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "profile": forms.URLInput(attrs={"class": "form-control"}),
            "gender": forms.TextInput(attrs={"class": "form-control"}),
            "zoneinfo": forms.TextInput(attrs={"class": "form-control"}),
            "locale": forms.TextInput(attrs={"class": "form-control"}),
            "street_address": forms.TextInput(attrs={"class": "form-control"}),
            "locality": forms.TextInput(attrs={"class": "form-control"}),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "picture": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class TOTPVerifyForm(forms.Form):
    """Token verifier for newly generated TOTP secrets."""

    token = forms.CharField(
        label="Authenticator code",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "one-time-code"}),
    )


class MailQuotaForm(forms.ModelForm):
    """Edit or create a MailQuota for an account."""

    class Meta:
        model = MailQuota
        fields = ("size_value", "suffix")
        widgets = {
            "size_value": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "suffix": forms.Select(attrs={"class": "form-select"}),
        }


class MailAliasForm(forms.ModelForm):
    """Add a mail alias for an account."""

    class Meta:
        model = MailAlias
        fields = ("alias",)
        widgets = {
            "alias": forms.EmailInput(attrs={"class": "form-control", "placeholder": "alias@example.com"}),
        }


class MailGroupForm(forms.ModelForm):
    """Create a new mail group."""

    class Meta:
        model = MailGroup
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Group name"}),
        }


class MailAccountCreateForm(forms.ModelForm):
    """Create a new mail account with required first and last names."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
        help_text="Password for the new account.",
        min_length=8,
    )

    class Meta:
        model = MailAccount
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "username"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "user@example.com"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "John"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Doe"}),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password or len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        return password

    def _post_clean(self):
        # Set password_hash before validation so the model's required field check passes
        raw_password = self.cleaned_data.get("password")
        if raw_password:
            self.instance.set_password(raw_password)
        super()._post_clean()


class AccountGroupsForm(forms.Form):
    """Assign groups for a single account."""

    groups = forms.ModelMultipleChoiceField(
        queryset=MailGroup.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "6"}),
    )


class ClientGroupsForm(forms.Form):
    """Assign groups and security settings for an OIDC client (access gating)."""

    groups = forms.ModelMultipleChoiceField(
        queryset=MailGroup.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )
    require_2fa = forms.BooleanField(
        required=False,
        label="Require Two-Factor Authentication",
        help_text="Users must complete TOTP verification to access this client",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


if Client:

    class OIDCClientCreateForm(forms.ModelForm):
        """Minimal client creator for OIDC Provider."""

        redirect_uris = forms.CharField(
            widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "https://app.example.com/callback"}),
            help_text="One URI per line.",
        )
        scope = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "openid email profile"}),
            help_text="Space-separated scopes. Leave blank for provider defaults.",
        )

        class Meta:
            model = Client
            fields = ("name", "client_id", "client_secret", "client_type", "response_types", "jwt_alg")
            widgets = {
                "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Client name"}),
                "client_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "client-id", "id": "id_client_id"}),
                "client_secret": forms.TextInput(attrs={"class": "form-control", "placeholder": "Generated secret", "id": "id_client_secret"}),
                "client_type": forms.Select(attrs={"class": "form-select"}),
                "response_types": forms.SelectMultiple(attrs={"class": "form-select", "size": "4"}),
                "jwt_alg": forms.Select(attrs={"class": "form-select"}),
            }

        def clean_client_id(self):
            client_id = self.cleaned_data.get("client_id")
            # Check uniqueness, excluding current instance if editing
            qs = Client.objects.filter(client_id=client_id)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This client ID already exists. Please choose a different one.")
            return client_id
else:
    OIDCClientCreateForm = None
