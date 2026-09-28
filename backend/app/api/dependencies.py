from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Assessment, Organisation


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

AccessToken = Annotated[
    str,
    Depends(oauth2_scheme),
]


def get_current_organisation(
    token: AccessToken,
    database: DatabaseSession,
) -> Organisation:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)

        if payload.get("type") != "access":
            raise credentials_error

        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise credentials_error

        organisation_id = int(subject)

    except (
        jwt.InvalidTokenError,
        TypeError,
        ValueError,
    ) as error:
        raise credentials_error from error

    organisation = database.get(
        Organisation,
        organisation_id,
    )

    if organisation is None:
        raise credentials_error

    return organisation


CurrentOrganisation = Annotated[
    Organisation,
    Depends(get_current_organisation),
]


def get_owned_assessment(
    assessment_id: int,
    organisation_id: int,
    database: DatabaseSession,
) -> Assessment:
    """Return the assessment if it belongs to the organisation, else 404."""
    assessment = database.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.organisation_id == organisation_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    return assessment
