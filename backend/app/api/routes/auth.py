import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentOrganisation
from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models import Organisation
from app.schemas.auth import (
    EmailVerificationResponse,
    OrganisationRegisterRequest,
    OrganisationResponse,
    ResendVerificationResponse,
    TokenResponse,
)


VERIFICATION_TOKEN_VALIDITY_HOURS = 24


def generate_verification_token() -> tuple[
    str, datetime
]:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(
        timezone.utc
    ) + timedelta(
        hours=VERIFICATION_TOKEN_VALIDITY_HOURS
    )

    return token, expires_at


router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "/register",
    response_model=OrganisationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_organisation(
    registration: OrganisationRegisterRequest,
    database: DatabaseSession,
) -> Organisation:
    normalised_email = registration.email.lower()
    normalised_name = registration.name.strip()

    existing_organisation = database.scalar(
        select(Organisation).where(
            func.lower(Organisation.email) == normalised_email
        )
    )

    if existing_organisation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    verification_token, verification_expires_at = (
        generate_verification_token()
    )

    organisation = Organisation(
    name=normalised_name,
    category=registration.category,
    email=normalised_email,
    password_hash=hash_password(
        registration.password
    ),
    is_verified=False,
    verification_token=verification_token,
    verification_expires_at=verification_expires_at,
)

    database.add(organisation)

    try:
        database.commit()
        database.refresh(organisation)

    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create this account.",
        ) from error

    return organisation


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_organisation(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    database: DatabaseSession,
) -> TokenResponse:
    normalised_email = form_data.username.lower()

    organisation = database.scalar(
        select(Organisation).where(
            func.lower(Organisation.email) == normalised_email
        )
    )

    if organisation is None or not verify_password(
        form_data.password,
        organisation.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        organisation_id=organisation.id,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=OrganisationResponse,
)
def get_current_account(
    organisation: CurrentOrganisation,
) -> Organisation:
    return organisation


@router.get(
    "/verify",
    response_model=EmailVerificationResponse,
)
def verify_organisation_email(
    token: str,
    database: DatabaseSession,
) -> EmailVerificationResponse:
    organisation = database.scalar(
        select(Organisation).where(
            Organisation.verification_token
            == token,
        )
    )

    if organisation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This verification link is "
                "invalid."
            ),
        )

    if organisation.is_verified:
        return EmailVerificationResponse(
            message=(
                "This account is already "
                "verified."
            ),
            is_verified=True,
        )

    expires_at = (
        organisation.verification_expires_at
    )

    if (
        expires_at is None
        or expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This verification link has "
                "expired. Request a new one from "
                "your account page."
            ),
        )

    organisation.is_verified = True
    organisation.verification_token = None
    organisation.verification_expires_at = None

    database.commit()

    return EmailVerificationResponse(
        message="Your organisation is now verified.",
        is_verified=True,
    )


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
)
def resend_verification(
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> ResendVerificationResponse:
    if organisation.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This account is already "
                "verified."
            ),
        )

    verification_token, verification_expires_at = (
        generate_verification_token()
    )

    organisation.verification_token = (
        verification_token
    )
    organisation.verification_expires_at = (
        verification_expires_at
    )

    database.commit()

    return ResendVerificationResponse(
        message=(
            "No email provider is configured "
            "for this prototype, so the "
            "verification link is shown below "
            "directly (per NFR11's email-failure "
            "fallback)."
        ),
        verification_token=verification_token,
    )