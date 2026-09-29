from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
    get_owned_assessment,
)
from app.models import (
    AssessmentQuestion,
    IndividualResponse,
    SurveySubmission,
)


router = APIRouter(
    tags=["submission management"],
)


class SubmissionListItem(BaseModel):
    submission_id: int
    respondent_group: str
    status: str
    answered_question_count: int
    total_question_count: int
    started_at: datetime
    submitted_at: datetime | None


class SubmissionListResponse(BaseModel):
    assessment_id: int
    submissions: list[SubmissionListItem]


class DeleteSubmissionResponse(BaseModel):
    submission_id: int
    deleted: bool
    message: str


@router.get(
    "/api/assessments/{assessment_id}/submissions",
    response_model=SubmissionListResponse,
)
def list_assessment_submissions(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> SubmissionListResponse:
    get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    total_question_count = (
        database.scalar(
            select(
                func.count(
                    AssessmentQuestion.id
                )
            ).where(
                AssessmentQuestion.assessment_id
                == assessment_id,
                AssessmentQuestion.is_active.is_(
                    True
                ),
            )
        )
        or 0
    )

    rows = database.execute(
        select(
            SurveySubmission,
            func.count(
                IndividualResponse.id
            ).label(
                "answered_question_count"
            ),
        )
        .outerjoin(
            IndividualResponse,
            IndividualResponse.submission_id
            == SurveySubmission.id,
        )
        .where(
            SurveySubmission.assessment_id
            == assessment_id,
        )
        .group_by(
            SurveySubmission.id,
        )
        .order_by(
            SurveySubmission.started_at.desc(),
        )
    ).all()

    submissions = [
        SubmissionListItem(
            submission_id=submission.id,
            respondent_group=(
                submission.respondent_group
            ),
            status=submission.status,
            answered_question_count=int(
                answered_question_count
            ),
            total_question_count=(
                total_question_count
            ),
            started_at=submission.started_at,
            submitted_at=submission.submitted_at,
        )
        for submission, answered_question_count
        in rows
    ]

    return SubmissionListResponse(
        assessment_id=assessment_id,
        submissions=submissions,
    )


@router.delete(
    "/api/assessments/{assessment_id}/submissions/{submission_id}",
    response_model=DeleteSubmissionResponse,
)
def delete_unfinished_submission(
    assessment_id: int,
    submission_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> DeleteSubmissionResponse:
    get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    submission = database.scalar(
        select(SurveySubmission).where(
            SurveySubmission.id
            == submission_id,
            SurveySubmission.assessment_id
            == assessment_id,
        )
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    if submission.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Submitted responses cannot "
                "be deleted."
            ),
        )

    database.delete(submission)
    database.commit()

    return DeleteSubmissionResponse(
        submission_id=submission_id,
        deleted=True,
        message=(
            "Unfinished submission deleted."
        ),
    )