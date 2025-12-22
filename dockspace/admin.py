import base64
from io import BytesIO

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from .models import ClientAccess, MailAccount, MailAlias, MailGroup, MailQuota



@admin.register(MailGroup)
class MailGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "member_count")
    search_fields = ("name", "members__email")
    filter_horizontal = ("members",)

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "Members"


@admin.register(ClientAccess)
class ClientAccessAdmin(admin.ModelAdmin):
    list_display = ("client", "group_list")
    search_fields = ("client__client_id", "client__name", "groups__name")
    filter_horizontal = ("groups",)

    def group_list(self, obj):
        return ", ".join(obj.groups.values_list("name", flat=True)) or "(no groups)"
    group_list.short_description = "Groups"


@admin.register(MailAlias)
class MailAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "recipient", "created_at", "updated_at")
    search_fields = ("alias", "user__email")

    def recipient(self, obj):
        return obj.recipient_email or "(no email)"
    recipient.short_description = "Recipient"


@admin.register(MailQuota)
class MailQuotaAdmin(admin.ModelAdmin):
    list_display = ("user", "quota_display", "created_at", "updated_at")
    search_fields = ("user__email",)

    def quota_display(self, obj):
        return obj.quota_string
    quota_display.short_description = "Quota"


class MailAccountAdminForm(forms.ModelForm):
    password_raw = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Enter a raw password to set {SHA512-CRYPT} on save.",
        label="Password",
    )

    class Meta:
        model = MailAccount
        fields = "__all__"
        required_css_class = "required"

    regenerate_totp = forms.BooleanField(
        required=False,
        help_text="Generate a new TOTP secret and reset verification.",
        label="Regenerate TOTP",
    )

    def clean(self):
        cleaned = super().clean()
        raw = cleaned.get("password_raw")
        account = self.instance
        # Hash early so model validation sees password_hash.
        if raw:
            account.set_password(raw)
            account._password_set_in_clean = True  # flag to avoid double-hashing in save
        else:
            # Enforce password entry on create when no existing hash.
            if not account.pk and not (account.password_hash or "").strip():
                self.add_error("password_raw", "Password is required.")
                # Avoid model clean raising missing password_hash when we already flagged the error.
                account._skip_password_required = True
        return cleaned

    def save(self, commit=True):
        account = super().save(commit=False)
        raw = self.cleaned_data.get("password_raw")
        regenerate_totp = self.cleaned_data.get("regenerate_totp")
        if raw and not getattr(account, "_password_set_in_clean", False):
            account.set_password(raw)
        if regenerate_totp or not account.totp_secret:
            import pyotp

            account.totp_secret = pyotp.random_base32()
            account.totp_last_counter = 0
            account.totp_verified_at = None
        if commit:
            account.save()
            self.save_m2m()
        return account


class MailQuotaInline(admin.StackedInline):
    model = MailQuota
    extra = 0
    max_num = 1
    can_delete = True


class MailAliasInline(admin.TabularInline):
    model = MailAlias
    extra = 0
    show_change_link = True
    fields = ("alias",)


class MailGroupMembershipInline(admin.TabularInline):
    model = MailGroup.members.through
    extra = 0
    verbose_name = "Mail group"
    verbose_name_plural = "Mail groups"
    fk_name = "mailaccount"


@admin.register(MailAccount)
class MailAccountAdmin(admin.ModelAdmin):
    form = MailAccountAdminForm
    inlines = [MailQuotaInline, MailAliasInline, MailGroupMembershipInline]
    actions = ["clear_totp"]
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "nickname",
        "email",
        "is_active",
        "is_admin",
        "password_hash",
        "phone_number",
        "phone_number_verified",
        "birthdate",
        "locale",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "nickname",
        "phone_number",
        "locality",
        "region",
        "country",
    )

    readonly_fields = (
        "password_hash",
        "totp_secret_display",
        "totp_provisioning_uri",
        "totp_qr",
        "picture_preview",
        "nickname",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "username",
                    "first_name",
                    "last_name",
                    "middle_name",
                    "email",
                    "is_active",
                    "is_admin",
                    "password_raw",
                    "password_hash",
                )
            },
        ),
        (
            "Profile",
            {
                "fields": (
                    "phone_number",
                    "phone_number_verified",
                    "profile",
                    "picture",
                    "picture_preview",
                    "website",
                    "gender",
                    "birthdate",
                    "zoneinfo",
                    "locale",
                    "street_address",
                    "locality",
                    "region",
                    "postal_code",
                    "country",
                )
            },
        ),
        (
            "TOTP",
            {
                "fields": (
                    "regenerate_totp",
                    "totp_secret_display",
                    "totp_provisioning_uri",
                    "totp_qr",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields += ("id", "created_at", "updated_at")

    def picture_preview(self, obj):
        if not obj or not obj.picture:
            return "(no image)"
        if not hasattr(obj.picture, "url"):
            return "(no image)"
        return format_html('<img src="{}" style="max-width: 160px; max-height: 160px;" />', obj.picture.url)

    picture_preview.short_description = "Picture"

    def totp_secret_display(self, obj):
        return obj.totp_secret or "(not set)"
    totp_secret_display.short_description = "TOTP secret"

    def _provisioning_uri(self, obj):
        if not obj or not obj.totp_secret or not obj.email:
            return None
        import pyotp

        issuer = getattr(settings, "OTP_TOTP_ISSUER", "")
        totp = pyotp.TOTP(obj.totp_secret)
        return totp.provisioning_uri(name=obj.email, issuer_name=issuer or None)

    def totp_provisioning_uri(self, obj):
        uri = self._provisioning_uri(obj)
        return uri or "(no secret)"
    totp_provisioning_uri.short_description = "Provisioning URI"

    def totp_qr(self, obj):
        uri = self._provisioning_uri(obj)
        if not uri:
            return "(no secret)"
        import qrcode

        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return format_html('<img src="data:image/png;base64,{}" alt="TOTP QR" />', encoded)

    totp_qr.short_description = "TOTP QR"

    def clear_totp(self, request, queryset):
        updated = queryset.update(totp_secret="", totp_verified_at=None, totp_last_counter=0)
        self.message_user(request, f"Cleared TOTP for {updated} account(s).")

    clear_totp.short_description = "Clear TOTP secret"
