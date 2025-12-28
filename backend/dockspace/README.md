# Dockspace Django Backend

## Overview

Dockspace is a mail server management application with OpenID Connect (OIDC) authentication, built using Django. This backend handles user authentication, mail account management, OIDC provider functionality, and integration with Docker Mailserver.

## Project Philosophy

### Code Organization Principles

1. **Modular Architecture**: Code is organized into functional modules (api, core, security, integrations)
2. **Clear Separation of Concerns**: Each module has a specific responsibility
3. **File Headers**: All Python files include descriptive headers explaining their purpose
4. **Type Safety**: We use type hints where appropriate to improve code clarity
5. **Security First**: Security-related code is isolated and properly validated

## Current Directory Structure

```
backend/dockspace/
├── README.md                    # This file - backend architecture documentation
├── __init__.py                  # Package initialization and model exports
├── apps.py                      # Django app configuration
├── admin.py                     # Django admin interface customizations
├── tests.py                     # Test suite
│
├── api/                         # REST API endpoints for Vue3 frontend
│   ├── __init__.py              # API package initialization
│   ├── audit.py                 # Audit log management endpoints
│   ├── auth.py                  # Authentication endpoints (login, logout, register, session)
│   ├── decorators.py            # Custom decorators for API endpoints
│   ├── mail.py                  # Mail account management endpoints
│   ├── oidc.py                  # OIDC-related endpoints and configuration
│   ├── profile.py               # User profile management endpoints
│   ├── sessions.py              # User session management endpoints
│   ├── settings.py              # Application settings endpoints
│   └── totp.py                  # TOTP/2FA management endpoints
│
├── core/                        # Core business logic and models
│   ├── __init__.py              # Core package initialization
│   ├── models.py                # Database models (MailAccount, MailAlias, MailQuota, AuditLog, etc.)
│   └── views.py                 # Core view functions (if needed beyond API)
│
├── security/                    # Security-related modules
│   ├── __init__.py              # Security package initialization
│   ├── auth_backend.py          # Custom authentication backend with TOTP support
│   ├── middleware.py            # Security middleware (CSP, domain settings, SMTP config)
│   └── validators.py            # Custom validators for security constraints
│
├── integrations/                # Third-party integrations
│   ├── __init__.py              # Integrations package initialization
│   ├── dms_export.py            # Docker Mailserver config file generation
│   ├── hooks.py                 # Post-save/delete hooks for external systems
│   ├── signals.py               # Django signals for keeping DMS configs in sync
│   └── userinfo.py              # OIDC userinfo endpoint customization
│
├── management/                  # Django management commands
│   ├── __init__.py              # Management package initialization
│   └── commands/                # Custom Django commands
│       ├── __init__.py          # Commands package initialization
│       ├── export_dms_files.py  # Export Docker Mailserver config files
│       ├── scan_dms_files.py    # Verify DMS config files are in sync
│       ├── set_mail_password.py # Set mail account password via CLI
│       └── test_oidc_flow.py    # Test OIDC authentication flow
│
├── migrations/                  # Django database migrations
│   ├── __init__.py              # Migrations package initialization
│   ├── 0001_initial.py          # Initial database schema
│   └── 0002_clientaccess_require_2fa.py  # Add 2FA requirement to client access
│
├── static/                      # Static files (compiled frontend)
│   └── dist/                    # Vue3 production build output
│       ├── assets/              # JS, CSS, and other assets
│       ├── images/              # Image assets
│       ├── index.html           # Frontend entry point
│       └── loader.css           # Loading screen styles
│
└── templates/                   # Django templates (minimal - mostly API-driven)
```

## Module Descriptions

### `api/` - REST API Layer

The API module contains all HTTP endpoints for the Vue3 frontend. Each file groups related endpoints:

- **audit.py**: Audit log querying and statistics (admin only)
- **auth.py**: User authentication flow (login, logout, registration, session management, setup)
- **decorators.py**: Custom decorators (@require_admin, etc.)
- **mail.py**: Mail account CRUD operations, alias management, quota management
- **oidc.py**: OIDC provider configuration and endpoints
- **profile.py**: User profile updates (name, picture, contact info, address)
- **sessions.py**: User session management and tracking
- **settings.py**: Application-wide settings management (SMTP, domain, session timeout)
- **totp.py**: Two-factor authentication setup and verification

**Conventions**:
- All endpoints return JSON responses
- Use `@require_http_methods()` decorator to enforce HTTP methods
- Use `@ensure_csrf_cookie` for endpoints that need CSRF protection
- Always validate input data before processing
- Return appropriate HTTP status codes (200, 400, 401, 403, 500)

### `core/` - Business Logic and Models

The core module contains database models and core business logic:

- **models.py**: Django ORM models for the application
  - `AppSettings`: Singleton model for global application configuration
  - `MailAccount`: Primary user/mail account model with OIDC profile claims
  - `MailAlias`: Email alias routing configuration
  - `MailQuota`: Per-user mailbox quota settings
  - `MailGroup`: User grouping for access control
  - `ClientAccess`: OIDC client access restrictions and 2FA requirements
  - `UserSession`: User session tracking for security monitoring
  - `AuditLog`: Comprehensive audit trail for all admin actions and security events

- **views.py**: Core view logic (currently minimal as most views are in `api/`)

**Conventions**:
- Models include comprehensive validation in `clean()` methods
- Use custom validators defined in `security/validators.py`
- All models have `created_at` and `updated_at` timestamps
- Override `save()` for complex save logic (password hashing, image processing)
- Use `__str__()` to provide meaningful string representations

### `security/` - Authentication and Security

The security module handles all authentication and security concerns:

- **auth_backend.py**: Custom Django authentication backend
  - Authenticates against `MailAccount` model
  - Supports TOTP two-factor authentication
  - Creates temporary Django `User` objects for OIDC compatibility

- **middleware.py**: Security middleware
  - `DomainSettingsMiddleware`: Dynamically updates ALLOWED_HOSTS and SMTP settings
  - `SecurityHeadersMiddleware`: Adds Content-Security-Policy headers

- **validators.py**: Custom field validators for security constraints
  - Email format validation
  - Password complexity requirements
  - Phone number format validation
  - Locale and timezone validation

**Security Conventions**:
- Passwords are stored as `{SHA512-CRYPT}` hashes for dovecot compatibility
- TOTP secrets are stored securely and never exposed in API responses
- All user input is validated before processing
- CSRF protection is enabled for state-changing operations

### `integrations/` - External System Integration

The integrations module manages connections to external systems:

- **dms_export.py**: Generates Docker Mailserver configuration files
  - `postfix-accounts.cf`: Mail account credentials
  - `postfix-virtual.cf`: Email alias mappings
  - `dovecot-quotas.cf`: Mailbox quota settings
  - Atomic file writes to prevent corruption
  - Drift detection and automatic sync

- **signals.py**: Django signal handlers
  - Auto-sync DMS config files when models change
  - Clean up conflicting aliases when mailboxes are created

- **userinfo.py**: OIDC UserInfo endpoint customization
  - Maps `MailAccount` fields to standard OIDC claims
  - Supports profile, email, phone, and address scopes

- **hooks.py**: Post-save/delete hooks for external integrations (future use)

**Integration Conventions**:
- Use Django signals for automatic sync operations
- Write config files atomically (write to temp, then rename)
- Log all integration operations for debugging
- Handle integration failures gracefully

### `management/commands/` - CLI Commands

Management commands for administrative tasks:

- **export_dms_files.py**: Manually export DMS config files
- **scan_dms_files.py**: Verify DMS files are in sync with database
- **set_mail_password.py**: Set mail account password from command line
- **test_oidc_flow.py**: Test OIDC authentication flow end-to-end

**Command Conventions**:
- Use `BaseCommand` class from Django
- Add `--help` descriptions for all arguments
- Use `self.stdout.write(self.style.SUCCESS(...))` for output
- Support `--dry-run` where applicable

## Database Models

### MailAccount (Primary User Model)

The `MailAccount` model is the primary user model for Dockspace. It stores:

- **Identity**: username, email, first_name, last_name, middle_name, nickname
- **Authentication**: password_hash (SHA512-CRYPT), totp_secret, totp_verified_at
- **Profile**: phone_number, picture, website, gender, birthdate
- **Localization**: zoneinfo, locale
- **Address**: street_address, locality, region, postal_code, country
- **Permissions**: is_active, is_admin
- **Django Compatibility**: Linked to Django `User` model via OneToOneField

### Supporting Models

- **AppSettings**: Singleton for global settings (SMTP, domain, session timeout)
- **MailAlias**: Email alias to mailbox routing
- **MailQuota**: Per-user mailbox size limits
- **MailGroup**: User grouping for access control
- **ClientAccess**: OIDC client restrictions (group membership, 2FA requirements)

## API Endpoint Patterns

All API endpoints follow these patterns:

```python
@require_http_methods(["POST"])
def endpoint_name(request):
    """
    Brief description of what this endpoint does.
    """
    try:
        data = json.loads(request.body)
        # Validate input
        # Process request
        # Return success response
        return JsonResponse({
            'success': True,
            'data': {...}
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
```

## Configuration Integration

The backend integrates with Docker Mailserver by generating config files:

1. **postfix-accounts.cf**: `email|{SHA512-CRYPT}hash`
2. **postfix-virtual.cf**: `alias@domain recipient@domain`
3. **dovecot-quotas.cf**: `email:10G`

These files are automatically synchronized when models change via Django signals.

## Adding New Files

When adding new files to the backend, follow these guidelines:

### 1. Choose the Correct Module

- **API endpoints** → `api/`
- **Database models** → `core/models.py` (or split into multiple files if needed)
- **Authentication/security logic** → `security/`
- **External integrations** → `integrations/`
- **Management commands** → `management/commands/`

### 2. Add File Header

Every Python file should start with a header comment:

```python
"""
Module: filename.py
Purpose: Brief description of what this module does

Detailed explanation if needed.
"""
```

### 3. Update This README

When adding new files or modules:

1. Update the "Current Directory Structure" section
2. Add description to the relevant "Module Descriptions" section
3. Document any new conventions or patterns
4. Update the "Recent Changes" section below

### 4. Follow Coding Conventions

- Use type hints for function parameters and return values
- Include docstrings for all functions and classes
- Validate all user input
- Use Django's built-in validators where possible
- Log important operations
- Write tests for new functionality

## File Header Template

Use this template for all new Python files:

```python
"""
Module: [filename.py]
Purpose: [One-line description]

[Detailed description of what this module does, what problems it solves,
and how it fits into the overall architecture. Include any important
notes about dependencies or side effects.]

Key Components:
- [Component 1]: [Description]
- [Component 2]: [Description]

Usage:
    [Example usage if applicable]

Author: [Your name]
Created: [Date]
"""
```

## Testing

Tests are located in `tests.py`. When adding new functionality:

1. Write unit tests for models (validation, methods)
2. Write integration tests for API endpoints
3. Test authentication flows thoroughly
4. Test edge cases and error handling

## Security Considerations

1. **Password Storage**: Passwords are stored as SHA512-CRYPT hashes
2. **CSRF Protection**: Enabled for all state-changing operations
3. **Input Validation**: All user input is validated before processing
4. **SQL Injection**: Use Django ORM to prevent SQL injection
5. **XSS Prevention**: Django templates auto-escape output
6. **HTTPS**: Production should always use HTTPS
7. **Session Security**: Sessions expire based on AppSettings.session_timeout

## Environment Variables

The backend expects these environment variables:

- `SECRET_KEY`: Django secret key for cryptographic signing
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `DATABASE_URL`: PostgreSQL connection string (optional, defaults to SQLite)
- `DMS_OUTPUT_DIR`: Directory for Docker Mailserver config files

## Recent Changes

### 2024-12-25
- Converted frontend from HTML templates to Vue3 SPA
- Restructured backend into modular architecture (api/, core/, security/, integrations/)
- Added comprehensive README documentation
- Added file headers to all Python files
- Implemented security hardening (CSP, CSRF, password validation)
- Added TOTP two-factor authentication support

## Audit Logging

### Overview

The audit logging system provides a comprehensive trail of all administrative actions and security-sensitive events in Dockspace. Every action is recorded with contextual information including who performed it, what was affected, when it occurred, and from where.

### AuditLog Model

The `AuditLog` model tracks:

- **Actor**: The MailAccount that performed the action (nullable for system actions)
- **Action**: Type of action performed (30+ predefined types)
- **Target**: What was affected (type, ID, and human-readable name)
- **Description**: Human-readable description of what happened
- **Metadata**: JSON field for additional structured data (before/after values, etc.)
- **Security Context**: IP address and user agent
- **Severity**: Classification as info, warning, or critical
- **Success**: Whether the action completed successfully
- **Timestamp**: When the action occurred

### Action Types

Actions are categorized by domain:

**Mail Account Actions**:
- `account.create`, `account.update`, `account.delete`
- `account.suspend`, `account.activate`
- `account.password_change`

**Mail Alias Actions**:
- `alias.create`, `alias.delete`

**Mail Group Actions**:
- `group.create`, `group.update`, `group.delete`
- `group.member_add`, `group.member_remove`

**Mail Quota Actions**:
- `quota.create`, `quota.update`, `quota.delete`

**OIDC Client Actions**:
- `oidc.create`, `oidc.update`, `oidc.delete`

**Application Settings**:
- `settings.update`, `settings.smtp_update`

**Authentication Actions**:
- `auth.login`, `auth.logout`, `auth.login_failed`
- `auth.2fa_enabled`, `auth.2fa_disabled`

**Session Actions**:
- `session.created`, `session.terminated`

### Using Audit Logging

To log an action, use the `AuditLog.log()` class method:

```python
from dockspace.core.models import AuditLog

# Example: Logging account creation
AuditLog.log(
    action='account.create',
    actor=request.user.mailaccount,
    target_type='MailAccount',
    target_id=new_account.id,
    target_name=new_account.email,
    description=f"Created mail account: {new_account.email}",
    metadata={
        'is_admin': new_account.is_admin,
        'quota': '5GB'
    },
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
    severity='info',  # 'info', 'warning', or 'critical'
    success=True
)
```

### Helper Function

For consistency, extract request metadata with a helper:

```python
def get_request_context(request):
    """Extract audit context from request."""
    return {
        'actor': getattr(request.user, 'mailaccount', None),
        'ip_address': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }
```

### When to Log

Log these types of events:

1. **All Administrative Actions**: Account/group/alias creation, updates, deletions
2. **Security Events**: Login attempts, 2FA changes, password changes
3. **Configuration Changes**: Settings updates, OIDC client modifications
4. **Authorization Failures**: Access denied events
5. **Critical Operations**: Account suspensions, admin privilege changes

### Audit Log Retention

- Audit logs are never automatically deleted
- They persist even when related objects are deleted (via SET_NULL)
- Consider implementing a retention policy based on your compliance requirements

### API Endpoints

Admin users can query audit logs via:

- `GET /api/audit/logs/` - List logs with filtering and pagination
- `GET /api/audit/stats/` - Get audit statistics and summaries

### Performance Considerations

- All audit writes are async (non-blocking)
- Database indexes on common query fields (actor, action, created_at, severity)
- Use pagination for large result sets
- Consider archiving old logs to separate storage

## Future Enhancements

Planned improvements to the backend:

1. **Enhanced Testing**: Increase test coverage to 90%+
2. **API Documentation**: Add OpenAPI/Swagger documentation
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **Email Verification**: Add email verification for new accounts
5. **Password Reset**: Implement secure password reset flow
6. **Multi-tenant Support**: Support multiple mail domains
7. **Background Tasks**: Use Celery for long-running tasks
8. **API Versioning**: Version the API for backward compatibility
9. **GraphQL Support**: Consider GraphQL as alternative to REST
10. **Audit Log Archival**: Automatic archival of old audit logs

## Maintenance Notes

### Keeping This README Updated

This README should be updated whenever:

1. New files or directories are added
2. Existing files are moved or renamed
3. Architecture patterns change
4. New conventions are established
5. Major features are added or removed

The person making the change is responsible for updating this README as part of their commit.

### Regular Reviews

This README should be reviewed quarterly to ensure it stays accurate and helpful.

## Getting Help

For questions about the backend architecture:

1. Check this README first
2. Look for similar patterns in existing code
3. Review Django documentation: https://docs.djangoproject.com/
4. Check OIDC Provider documentation: https://django-oidc-provider.readthedocs.io/

## Contributing

When contributing to the backend:

1. Follow the established directory structure
2. Add file headers to all new files
3. Update this README if you add/change structure
4. Write tests for new functionality
5. Validate all user input
6. Log important operations
7. Use type hints and docstrings
