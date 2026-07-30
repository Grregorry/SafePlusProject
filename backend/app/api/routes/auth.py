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
    OrganisationRegisterRequest,
    OrganisationResponse,
    TokenResponse,
)


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

    organisation = Organisation(
    name=normalised_name,
    category=registration.category,
    email=normalised_email,
    password_hash=hash_password(
        registration.password
    ),
    is_verified=False,
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