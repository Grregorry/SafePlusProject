from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
)
from app.models.assessment import Assessment
from app.models.assessment_question import AssessmentQuestion
from app.models.question import Question
from app.models.response_count import ResponseCount
from app.schemas.assessment_progress import (
    AssessmentProgressResponse,
    QuestionProgressResponse,
)


router = APIRouter(
    prefix="/api/assessments",
    tags=["assessment progress"],
)


def get_owned_assessment(
    assessment_id: int,
    organisation_id: int,
    database: DatabaseSession,
) -> Assessment:
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


@router.get(
    "/{assessment_id}/progress",
    response_model=AssessmentProgressResponse,
)
def get_assessment_progress(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> AssessmentProgressResponse:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    active_question_rows = list(
        database.execute(
            select(
                AssessmentQuestion,
                Question,
            )
            .join(
                Question,
                AssessmentQuestion.question_id == Question.id,
            )
            .where(
                AssessmentQuestion.assessment_id == assessment.id,
                AssessmentQuestion.is_active.is_(True),
            )
            .order_by(Question.id)
        ).all()
    )

    question_progress: list[QuestionProgressResponse] = []

    employee_complete_count = 0
    manager_complete_count = 0
    fully_complete_count = 0

    for assessment_question, question in active_question_rows:
        response_groups = set(
            database.scalars(
                select(ResponseCount.respondent_group).where(
                    ResponseCount.assessment_question_id
                    == assessment_question.id,
                    ResponseCount.count > 0,
                    ResponseCount.response_option != "N/A",
                )
            ).all()
        )

        employee_complete = "Employee" in response_groups
        manager_complete = "Senior Manager" in response_groups

        fully_complete = (
            employee_complete and manager_complete
        )

        if employee_complete:
            employee_complete_count += 1

        if manager_complete:
            manager_complete_count += 1

        if fully_complete:
            fully_complete_count += 1

        question_progress.append(
            QuestionProgressResponse(
                question_id=question.id,
                question_number=question.question_number,
                employee_complete=employee_complete,
                manager_complete=manager_complete,
                fully_complete=fully_complete,
            )
        )

    active_question_count = len(active_question_rows)

    if active_question_count == 0:
        progress_percentage = 0
    else:
        progress_percentage = round(
            (
                fully_complete_count
                / active_question_count
            )
            * 100
        )

    return AssessmentProgressResponse(
        assessment_id=assessment.id,
        active_question_count=active_question_count,
        employee_complete_count=employee_complete_count,
        manager_complete_count=manager_complete_count,
        fully_complete_count=fully_complete_count,
        overall_progress_percentage=progress_percentage,
        questions=question_progress,
    )