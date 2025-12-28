"""
Custom validators for enhanced security.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    """
    Validates that a password meets complexity requirements:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    This validator enhances security beyond Django's built-in validators.
    """

    def validate(self, password, user=None):
        errors = []

        if not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one uppercase letter."),
                    code='password_no_upper',
                )
            )
        if not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one lowercase letter."),
                    code='password_no_lower',
                )
            )
        if not re.search(r'\d', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one digit."),
                    code='password_no_digit',
                )
            )
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one special character (!@#$%^&* etc.)."),
                    code='password_no_special',
                )
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )
