"""Unit tests: authentication flows (registration, login, session
tokens, email verification and account isolation)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.session import SessionLocal
from app.models import Organisation

from .helpers import PASSWORD, auth_headers, create_assessment, login, register

AREA = "auth"


def me(client, token):
    return client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})


def stored_organisation(email):
    with SessionLocal() as database:
        return database.scalar(select(Organisation).where(Organisation.email == email))


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-01",
    title="Passwords are stored as a salted hash",
    input=f"hash_password('{PASSWORD}') twice",
    expected="Hash differs from the password and between calls; both verify",
)
def test_password_hashing(evidence):
    first = hash_password(PASSWORD)
    second = hash_password(PASSWORD)
    evidence("actual", f"{first[:16]}… / {second[:16]}…; verify → {verify_password(PASSWORD, first)}")
    assert first != PASSWORD and first != second
    assert verify_password(PASSWORD, first) and verify_password(PASSWORD, second)


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-02",
    title="A wrong password does not verify",
    input="verify_password('wrong-password', hash)",
    expected="False",
)
def test_wrong_password(evidence):
    result = verify_password("wrong-password", hash_password(PASSWORD))
    evidence("actual", str(result))
    assert result is False


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-03",
    title="Access token holds the organisation, type and expiry",
    input="create_access_token(organisation_id=42)",
    expected=f"sub '42', type 'access', expires in {settings.access_token_expire_minutes} minutes",
)
def test_token_contents(evidence):
    payload = decode_access_token(create_access_token(organisation_id=42))
    minutes = (datetime.fromtimestamp(payload["exp"], UTC) - datetime.now(UTC)).total_seconds() / 60
    evidence("actual", f"sub '{payload['sub']}', type '{payload['type']}', expires in {minutes:.1f} minutes")
    assert payload["sub"] == "42" and payload["type"] == "access"
    assert abs(minutes - settings.access_token_expire_minutes) < 1


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-04",
    title="Register a new organisation",
    input="'  Acme   Builders ', 'Owner@Example.com', Construction",
    expected="201; name tidied, email lower-cased, unverified; no password in response",
)
def test_register(client, evidence):
    response = register(client, "Owner@Example.com", name="  Acme   Builders ")
    body = response.json()
    evidence("actual", f"{response.status_code}; name '{body.get('name')}', email '{body.get('email')}', is_verified {body.get('is_verified')}; keys {sorted(body)}")
    assert response.status_code == 201
    assert body["name"] == "Acme Builders"
    assert body["email"] == "owner@example.com"
    assert body["is_verified"] is False
    assert not any("password" in key for key in body)


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-05",
    title="The same email cannot register twice (any letter case)",
    input="owner@example.com, then OWNER@example.com",
    expected="409 'An account with this email already exists.'",
)
def test_duplicate_email(client, evidence):
    register(client, "owner@example.com")
    response = register(client, "OWNER@example.com")
    evidence("actual", f"{response.status_code} {response.json()['detail']!r}")
    assert response.status_code == 409


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-06",
    title="Invalid registration details are rejected",
    input="7-character password; malformed email; unknown category; 1-character name",
    expected="422 for each",
)
def test_invalid_registration(client, evidence):
    results = {
        "short password": register(client, "a@example.com", password="short12").status_code,
        "bad email": register(client, "not-an-email").status_code,
        "unknown category": register(client, "b@example.com", category="Space travel").status_code,
        "short name": register(client, "c@example.com", name=" x ").status_code,
    }
    evidence("actual", ", ".join(f"{k} → {v}" for k, v in results.items()))
    assert set(results.values()) == {422}


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-07",
    title="Log in with the correct details (email in any case)",
    input="OWNER@EXAMPLE.COM + correct password",
    expected=f"200, bearer token, expires_in {settings.access_token_expire_minutes * 60}",
)
def test_login_success(client, evidence):
    register(client, "owner@example.com")
    response = login(client, "OWNER@EXAMPLE.COM")
    body = response.json()
    evidence("actual", f"{response.status_code}, token_type {body.get('token_type')}, expires_in {body.get('expires_in')}")
    assert response.status_code == 200
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["expires_in"] == settings.access_token_expire_minutes * 60


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-08",
    title="Wrong password and unknown email give the same answer",
    input="Registered email + wrong password; unregistered email",
    expected="401 'Incorrect email or password.' for both (no account enumeration)",
)
def test_login_failures(client, evidence):
    register(client, "owner@example.com")
    wrong = login(client, "owner@example.com", password="Wrong-Password-1")
    unknown = login(client, "nobody@example.com")
    evidence("actual", f"{wrong.status_code} {wrong.json()['detail']!r}; {unknown.status_code} {unknown.json()['detail']!r}")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-09",
    title="A valid token opens the account",
    input="GET /api/auth/me with the login token",
    expected="200 with the organisation's own details",
)
def test_me(client, evidence):
    register(client, "owner@example.com", name="Acme Builders")
    token = login(client, "owner@example.com").json()["access_token"]
    response = me(client, token)
    evidence("actual", f"{response.status_code} {response.json().get('name')}")
    assert response.status_code == 200 and response.json()["email"] == "owner@example.com"


def _forged(payload):
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-10",
    title="Missing, expired, tampered, wrong-type and orphaned tokens are refused",
    input="No token; expired 1 minute ago; bad signature; type 'refresh'; organisation that doesn't exist",
    expected="401 for each",
)
def test_rejected_tokens(client, evidence):
    register(client, "owner@example.com")
    organisation_id = stored_organisation("owner@example.com").id
    valid = login(client, "owner@example.com").json()["access_token"]

    results = {
        "no token": client.get("/api/auth/me").status_code,
        "expired": me(client, _forged({"sub": str(organisation_id), "type": "access", "exp": datetime.now(UTC) - timedelta(minutes=1)})).status_code,
        "tampered": me(client, valid.rsplit(".", 1)[0] + "." + "A" * 43).status_code,
        "wrong type": me(client, _forged({"sub": str(organisation_id), "type": "refresh", "exp": datetime.now(UTC) + timedelta(minutes=5)})).status_code,
        "orphaned": me(client, create_access_token(organisation_id=999999)).status_code,
    }
    evidence("actual", ", ".join(f"{k} → {v}" for k, v in results.items()))
    assert set(results.values()) == {401}


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-11",
    title="Email verification link verifies the account once",
    input="GET /api/auth/verify?token=<issued token>, then the same link again",
    expected="200 verified, token cleared; second use 400 'invalid'",
)
def test_verify(client, evidence):
    register(client, "owner@example.com")
    token = stored_organisation("owner@example.com").verification_token
    first = client.get("/api/auth/verify", params={"token": token})
    organisation = stored_organisation("owner@example.com")
    second = client.get("/api/auth/verify", params={"token": token})
    evidence("actual", f"{first.status_code} {first.json()}; stored token {organisation.verification_token}; second {second.status_code}")
    assert first.status_code == 200 and first.json()["is_verified"] is True
    assert organisation.is_verified and organisation.verification_token is None
    assert second.status_code == 400


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-12",
    title="Expired and unknown verification links are refused",
    input="Link older than 24 hours; made-up link",
    expected="400 'expired' and 400 'invalid'; account stays unverified",
)
def test_verify_rejected(client, evidence):
    register(client, "owner@example.com")

    with SessionLocal() as database:
        organisation = database.scalar(select(Organisation).where(Organisation.email == "owner@example.com"))
        organisation.verification_expires_at = datetime.now(UTC) - timedelta(minutes=1)
        token = organisation.verification_token
        database.commit()

    expired = client.get("/api/auth/verify", params={"token": token})
    unknown = client.get("/api/auth/verify", params={"token": "made-up"})
    evidence("actual", f"{expired.status_code} {expired.json()['detail']!r}; {unknown.status_code} {unknown.json()['detail']!r}")
    assert expired.status_code == 400 and "expired" in expired.json()["detail"]
    assert unknown.status_code == 400 and "invalid" in unknown.json()["detail"]
    assert stored_organisation("owner@example.com").is_verified is False


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-13",
    title="Requesting a new verification link replaces the old one",
    input="POST /api/auth/resend-verification, then try the old and new links",
    expected="New link returned; old link 400; new link verifies; resending once verified 409",
)
def test_resend_verification(client, evidence):
    headers = auth_headers(client)
    old_token = stored_organisation("owner@example.com").verification_token
    resend = client.post("/api/auth/resend-verification", headers=headers)
    new_token = resend.json()["verification_token"]
    old = client.get("/api/auth/verify", params={"token": old_token})
    new = client.get("/api/auth/verify", params={"token": new_token})
    again = client.post("/api/auth/resend-verification", headers=headers)
    evidence("actual", f"resend {resend.status_code}; old link {old.status_code}; new link {new.status_code}; resend when verified {again.status_code}")
    assert resend.status_code == 200 and new_token != old_token
    assert old.status_code == 400 and new.status_code == 200
    assert again.status_code == 409


@pytest.mark.qa(
    area=AREA,
    id="UT-AU-14",
    title="An organisation cannot see another organisation's assessments",
    input="Organisation B requests Organisation A's assessment and its report",
    expected="404 for both; B's list is empty",
)
def test_organisation_isolation(client, evidence):
    owner = auth_headers(client, "a@example.com", name="Company A")
    other = auth_headers(client, "b@example.com", name="Company B")
    assessment = create_assessment(client, owner)

    get = client.get(f"/api/assessments/{assessment['id']}", headers=other)
    report = client.get(f"/api/assessments/{assessment['id']}/report", headers=other)
    listing = client.get("/api/assessments", headers=other).json()
    evidence("actual", f"get {get.status_code}, report {report.status_code}, B's list has {len(listing)}")
    assert get.status_code == 404 and report.status_code == 404
    assert listing == []
