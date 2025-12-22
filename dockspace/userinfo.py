from django.utils import timezone

from .models import MailAccount


def userinfo(claims, principal):
    """Supply OIDC claim fields from MailAccount; fallback by matching email."""
    account = None
    if isinstance(principal, MailAccount):
        account = principal
    else:
        email = getattr(principal, "email", "") or None
        if email:
            account = MailAccount.objects.filter(email__iexact=email).first()

    if account is None:
        return claims

    username = account.username or account.email
    full_name = " ".join([p for p in [account.first_name, account.middle_name, account.last_name] if p]).strip()

    claims["name"] = claims.get("name") or (full_name or username)
    claims["given_name"] = claims.get("given_name") or (account.first_name or None)
    claims["family_name"] = claims.get("family_name") or (account.last_name or None)
    claims["middle_name"] = claims.get("middle_name") or (account.middle_name or None)
    claims["nickname"] = claims.get("nickname") or (account.nickname or username)
    claims["preferred_username"] = claims.get("preferred_username") or username
    claims.setdefault("profile", None)
    claims["profile"] = claims.get("profile") or (account.profile or None)
    updated_at = account.updated_at or timezone.now()
    claims["updated_at"] = int(updated_at.timestamp())

    email = account.email
    claims["email"] = claims.get("email") or email
    claims["email_verified"] = claims.get("email_verified")
    if claims["email_verified"] is None:
        claims["email_verified"] = bool(email)

    claims["phone_number"] = claims.get("phone_number") or (account.phone_number or None)
    claims["phone_number_verified"] = bool(claims.get("phone_number_verified") or account.phone_number_verified)

    picture_url = None
    if getattr(account, "picture", None):
        try:
            picture_url = account.picture.url
        except Exception:
            picture_url = None
    claims["picture"] = claims.get("picture") or picture_url
    claims["website"] = claims.get("website") or (account.website or None)
    claims["gender"] = claims.get("gender") or (account.gender or None)
    claims["birthdate"] = claims.get("birthdate") or (account.birthdate.isoformat() if account.birthdate else None)
    claims["zoneinfo"] = claims.get("zoneinfo") or (account.zoneinfo or None)
    claims["locale"] = claims.get("locale") or (account.locale or None)

    address_claim = claims.get("address") or {}
    address_claim.setdefault("formatted", None)
    address_claim["street_address"] = address_claim.get("street_address") or (account.street_address or None)
    address_claim["locality"] = address_claim.get("locality") or (account.locality or None)
    address_claim["region"] = address_claim.get("region") or (account.region or None)
    address_claim["postal_code"] = address_claim.get("postal_code") or (account.postal_code or None)
    address_claim["country"] = address_claim.get("country") or (account.country or None)
    parts = [
        address_claim.get("street_address") or "",
        address_claim.get("locality") or "",
        address_claim.get("region") or "",
        address_claim.get("postal_code") or "",
        address_claim.get("country") or "",
    ]
    formatted = ", ".join([p for p in parts if p.strip()])
    address_claim["formatted"] = address_claim.get("formatted") or (formatted or None)
    claims["address"] = address_claim

    return claims
