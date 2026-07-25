from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
)
from app.models import Assessment
from app.schemas.assessment import AssessmentResponse


router = APIRouter(
    prefix="/api/assessments",
    tags=["assessments"],
)


@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> Assessment:
    assessment = Assessment(
        organisation_id=organisation.id,
        status="draft",
    )

    database.add(assessment)
    database.commit()
    database.refresh(assessment)

    return assessment


@router.get(
    "",
    response_model=list[AssessmentResponse],
)
def get_assessments(
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> list[Assessment]:
    statement = (
        select(Assessment)
        .where(
            Assessment.organisation_id == organisation.id
        )
        .order_by(Assessment.created_at.desc())
    )

    return list(database.scalars(statement).all())