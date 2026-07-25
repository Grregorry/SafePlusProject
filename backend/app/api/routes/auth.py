from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models import Organisation
from app.schemas.auth import (
    OrganisationRegisterRequest,
    OrganisationResponse,
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
            func.lower(Organisation.email)
            == normalised_email
        )
    )

    if existing_organisation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    organisation = Organisation(
        name=normalised_name,
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