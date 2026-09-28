from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
    get_owned_assessment,
)
from app.models.assessment_question import AssessmentQuestion
from app.models.manual_response_count import ManualResponseCount
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
    digital_employee_complete_count = 0
    digital_manager_complete_count = 0
    manual_employee_complete_count = 0
    manual_manager_complete_count = 0

    def manual_entries_for_group(
        assessment_question_id: int,
        respondent_group: str,
    ) -> int:
        return database.scalar(
            select(
                func.coalesce(
                    func.sum(ManualResponseCount.count),
                    0,
                )
            ).where(
                ManualResponseCount.assessment_question_id
                == assessment_question_id,
                ManualResponseCount.respondent_group
                == respondent_group,
                ManualResponseCount.response_option != "N/A",
            )
        ) or 0

    for assessment_question, question in active_question_rows:
        digital_response_groups = set(
            database.scalars(
                select(ResponseCount.respondent_group).where(
                    ResponseCount.assessment_question_id
                    == assessment_question.id,
                    ResponseCount.count > 0,
                    ResponseCount.response_option != "N/A",
                )
            ).all()
        )

        employee_manual_entries_recorded = (
            manual_entries_for_group(
                assessment_question.id,
                "Employee",
            )
        )

        manager_manual_entries_recorded = (
            manual_entries_for_group(
                assessment_question.id,
                "Senior Manager",
            )
        )

        employee_digital_present = (
            "Employee" in digital_response_groups
        )

        manager_digital_present = (
            "Senior Manager" in digital_response_groups
        )

        employee_manual_target_met = (
            assessment.expected_manual_entries_employee
            == 0
            or employee_manual_entries_recorded
            == assessment.expected_manual_entries_employee
        )

        manager_manual_target_met = (
            assessment.expected_manual_entries_manager
            == 0
            or manager_manual_entries_recorded
            == assessment.expected_manual_entries_manager
        )

        employee_complete = (
            employee_digital_present
            or employee_manual_entries_recorded > 0
        ) and employee_manual_target_met

        manager_complete = (
            manager_digital_present
            or manager_manual_entries_recorded > 0
        ) and manager_manual_target_met

        fully_complete = (
            employee_complete and manager_complete
        )

        if employee_complete:
            employee_complete_count += 1

        if manager_complete:
            manager_complete_count += 1

        if fully_complete:
            fully_complete_count += 1

        if employee_digital_present:
            digital_employee_complete_count += 1

        if manager_digital_present:
            digital_manager_complete_count += 1

        if employee_manual_entries_recorded > 0:
            manual_employee_complete_count += 1

        if manager_manual_entries_recorded > 0:
            manual_manager_complete_count += 1

        question_progress.append(
            QuestionProgressResponse(
                question_id=question.id,
                question_number=question.question_number,
                employee_complete=employee_complete,
                manager_complete=manager_complete,
                employee_manual_entries_recorded=(
                    employee_manual_entries_recorded
                ),
                manager_manual_entries_recorded=(
                    manager_manual_entries_recorded
                ),
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
        expected_manual_entries_employee=(
            assessment.expected_manual_entries_employee
        ),
        expected_manual_entries_manager=(
            assessment.expected_manual_entries_manager
        ),
        digital_employee_complete_count=(
            digital_employee_complete_count
        ),
        digital_manager_complete_count=(
            digital_manager_complete_count
        ),
        manual_employee_complete_count=(
            manual_employee_complete_count
        ),
        manual_manager_complete_count=(
            manual_manager_complete_count
        ),
        questions=question_progress,
    )