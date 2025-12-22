import json
import urllib.parse

from django.core.management.base import BaseCommand, CommandError
from django.test import Client as DjangoClient
from django.test.utils import override_settings
from django.urls import reverse

from dockspace.models import ClientAccess, MailAccount, MailGroup, MailQuota
import jwt
from oidc_provider.models import Client, ResponseType


class Command(BaseCommand):
    help = (
        "Creates a test user and OIDC client, then runs an end-to-end "
        "authorization code flow using Django's test client."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", default="testuser")
        parser.add_argument("--email", default="testuser@example.com")
        parser.add_argument("--password", default="testpass123")
        parser.add_argument("--client-id", dest="client_id", default="test-client")
        parser.add_argument("--client-secret", dest="client_secret", default="test-secret")
        parser.add_argument(
            "--redirect-uri",
            dest="redirect_uri",
            default="http://localhost:8000/oidc/callback",
        )
        parser.add_argument(
            "--group-name",
            dest="group_name",
            default="oidc-test-access",
            help="Group required to use the client (created if missing).",
        )
        parser.add_argument("--phone-number", dest="phone_number", default="555-555-1234")
        parser.add_argument("--phone-verified", dest="phone_verified", action="store_true")
        parser.add_argument("--street-address", dest="street_address", default="123 Test St")
        parser.add_argument("--locality", dest="locality", default="Testville")
        parser.add_argument("--region", dest="region", default="TS")
        parser.add_argument("--postal-code", dest="postal_code", default="00000")
        parser.add_argument("--country", dest="country", default="US")
        parser.add_argument("--picture-url", dest="picture_url", default="", help="(unused, kept for compatibility)")
        parser.add_argument("--website", dest="website", default="https://example.com")
        parser.add_argument("--gender", dest="gender", default="unspecified")
        parser.add_argument("--birthdate", dest="birthdate", default="1990-01-01")
        parser.add_argument("--zoneinfo", dest="zoneinfo", default="UTC")
        parser.add_argument("--locale", dest="locale", default="en-US")

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        password = options["password"]
        client_id = options["client_id"]
        client_secret = options["client_secret"]
        redirect_uri = options["redirect_uri"]
        group_name = options["group_name"]
        phone_number = options["phone_number"]
        phone_verified = options["phone_verified"]
        street_address = options["street_address"]
        locality = options["locality"]
        region = options["region"]
        postal_code = options["postal_code"]
        country = options["country"]
        picture_url = options["picture_url"]
        website = options["website"]
        gender = options["gender"]
        birthdate = options["birthdate"]
        zoneinfo = options["zoneinfo"]
        locale = options["locale"]

        user = self._ensure_account(username, email, password)
        client = self._ensure_client(client_id, client_secret, redirect_uri)
        self._ensure_group_access(client, group_name, user)
        self._ensure_profile(
            user,
            phone_number,
            phone_verified,
            street_address,
            locality,
            region,
            postal_code,
            country,
            website,
            gender,
            birthdate,
            zoneinfo,
            locale,
        )

        self.stdout.write(self.style.MIGRATE_HEADING("Running authorization code flow..."))
        self._run_flow(user, password, client, redirect_uri)
        self.stdout.write(self.style.SUCCESS("Flow completed successfully."))

    def _ensure_account(self, username, email, password):
        account, created = MailAccount.objects.get_or_create(email=email or username)
        account.username = username or account.username or account.email
        account.email = email or account.email or account.username
        account.nickname = account.username
        account.first_name = account.first_name or account.username
        account.last_name = account.last_name or "User"
        account.set_password(password)
        account.save()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created mail account {account.email}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Updated password for {account.email}"))
        return account

    def _ensure_client(self, client_id, client_secret, redirect_uri):
        response_type_code, _ = ResponseType.objects.get_or_create(value="code")
        client, created = Client.objects.get_or_create(client_id=client_id)
        client.name = client.name or "Test Client"
        client.client_secret = client_secret
        client.client_type = "confidential"
        client._redirect_uris = redirect_uri
        client._post_logout_redirect_uris = redirect_uri
        client._scope = "openid profile email phone address offline_access"
        client.require_consent = False
        client.save()
        client.response_types.set([response_type_code])
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created OIDC client {client_id}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Updated OIDC client {client_id}"))
        return client

    def _ensure_group_access(self, client, group_name, user):
        group, _ = MailGroup.objects.get_or_create(name=group_name)
        cga, created = ClientAccess.objects.get_or_create(client=client)
        cga.groups.add(group)
        group.members.add(user)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Attached group access to client {client.client_id}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Ensured group access on client {client.client_id}"))

    def _ensure_profile(
        self,
        account,
        phone_number,
        phone_verified,
        street_address,
        locality,
        region,
        postal_code,
        country,
        website,
        gender,
        birthdate,
        zoneinfo,
        locale,
    ):
        account.phone_number = phone_number
        account.phone_number_verified = phone_verified
        account.street_address = street_address
        account.locality = locality
        account.region = region
        account.postal_code = postal_code
        account.country = country
        account.website = website
        account.gender = gender
        account.zoneinfo = zoneinfo
        account.locale = locale
        try:
            from datetime import date
            year, month, day = [int(x) for x in birthdate.split("-")]
            account.birthdate = date(year, month, day)
        except Exception:
            account.birthdate = None
        account.save()
        MailQuota.objects.get_or_create(user=account, defaults={"size_value": 10, "suffix": "G"})
        self.stdout.write(self.style.NOTICE(f"Updated MailAccount profile for {account.email}"))

    def _run_flow(self, user, password, client, redirect_uri):
        auth_url = reverse("oidc_provider:authorize")
        token_url = reverse("oidc_provider:token")

        params = {
            "client_id": client.client_id,
            "response_type": "code",
            "scope": "openid profile email phone address",
            "state": "demo-state",
            "nonce": "demo-nonce",
            "redirect_uri": redirect_uri,
        }

        with override_settings(OIDC_SKIP_CONSENT_ALWAYS=True):
            session_client = DjangoClient()
            if not session_client.login(username=user.email, password=password):
                raise CommandError("Login failed for test user.")

            response = session_client.get(auth_url, params)
            if response.status_code != 302:
                raise CommandError(f"Authorization failed: {response.status_code} {response.content}")

            location = response["Location"]
            parsed = urllib.parse.urlparse(location)
            query = urllib.parse.parse_qs(parsed.query)
            code = query.get("code", [None])[0]
            state = query.get("state", [None])[0]

            self.stdout.write(self.style.HTTP_INFO(f"Authorize redirect: {location}"))
            self.stdout.write(f"Code: {code}")
            self.stdout.write(f"State: {state}")
            if not code:
                raise CommandError(f"Authorization response missing code: {location}")

            token_resp = session_client.post(
                token_url,
                {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client.client_id,
                    "client_secret": client.client_secret,
                },
            )
            if token_resp.status_code != 200:
                raise CommandError(
                    f"Token exchange failed: {token_resp.status_code} {token_resp.content}"
                )

            tokens = token_resp.json()
            self.stdout.write(self.style.HTTP_INFO("Authorization code flow succeeded."))
            self.stdout.write("Token response:")
            self.stdout.write(json.dumps(tokens, indent=2))

            id_token = tokens.get("id_token")
            if id_token:
                claims = jwt.decode(id_token, options={"verify_signature": False, "verify_aud": False})
                self.stdout.write("ID token claims (decoded, signature not verified):")
                self.stdout.write(json.dumps(claims, indent=2))
