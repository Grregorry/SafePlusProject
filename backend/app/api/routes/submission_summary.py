from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
)
from app.models import Assessment, SurveySubmission


router = APIRouter(
    tags=["assessment submission summary"],
)


class SubmissionSummaryResponse(BaseModel):
    assessment_id: int
    employee_submitted: int
    senior_manager_submitted: int
    submitted_total: int
    employee_in_progress: int
    senior_manager_in_progress: int
    in_progress_total: int
    started_total: int


@router.get(
    "/api/assessments/{assessment_id}/submission-summary",
    response_model=SubmissionSummaryResponse,
)
def get_submission_summary(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> SubmissionSummaryResponse:
    assessment = database.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.organisation_id == organisation.id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    employee_submitted = database.scalar(
        select(func.count(SurveySubmission.id)).where(
            SurveySubmission.assessment_id == assessment_id,
            SurveySubmission.respondent_group == "Employee",
            SurveySubmission.status == "submitted",
        )
    ) or 0

    senior_manager_submitted = database.scalar(
        select(func.count(SurveySubmission.id)).where(
            SurveySubmission.assessment_id == assessment_id,
            SurveySubmission.respondent_group == "Senior Manager",
            SurveySubmission.status == "submitted",
        )
    ) or 0

    employee_in_progress = database.scalar(
        select(func.count(SurveySubmission.id)).where(
            SurveySubmission.assessment_id == assessment_id,
            SurveySubmission.respondent_group == "Employee",
            SurveySubmission.status == "in_progress",
        )
    ) or 0

    senior_manager_in_progress = database.scalar(
        select(func.count(SurveySubmission.id)).where(
            SurveySubmission.assessment_id == assessment_id,
            SurveySubmission.respondent_group == "Senior Manager",
            SurveySubmission.status == "in_progress",
        )
    ) or 0

    submitted_total = (
        employee_submitted
        + senior_manager_submitted
    )

    in_progress_total = (
        employee_in_progress
        + senior_manager_in_progress
    )

    return SubmissionSummaryResponse(
        assessment_id=assessment_id,
        employee_submitted=employee_submitted,
        senior_manager_submitted=senior_manager_submitted,
        submitted_total=submitted_total,
        employee_in_progress=employee_in_progress,
        senior_manager_in_progress=senior_manager_in_progress,
        in_progress_total=in_progress_total,
        started_total=submitted_total + in_progress_total,
    )