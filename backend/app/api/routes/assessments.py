from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
)
from app.models import (
    AIAnalysis,
    Assessment,
    AssessmentQuestion,
    Domain,
    Question,
    ResponseCount,
)

from app.services.assessment_report import (
    generate_assessment_report,
)
from app.models.question_score import QuestionScore
from app.schemas.assessment import (
    AssessmentCompletionResponse,
    AssessmentCreateRequest,
    AssessmentQuestionSetupResponse,
    AssessmentResponse,
    AssessmentScoringResponse,
    IncompleteQuestionResponse,
    QuestionResponsesResponse,
    QuestionResponsesUpdate,
    ResponseCountResponse,
    SituationQuestionSelectionRequest,
)
from app.services.scoring import calculate_assessment_scores


router = APIRouter(
    prefix="/api/assessments",
    tags=["assessments"],
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


def ensure_assessment_is_editable(
    assessment: Assessment,
) -> None:
    if assessment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed assessments cannot be edited.",
        )


def initialise_compulsory_questions(
    assessment: Assessment,
    database: DatabaseSession,
) -> None:
    existing_question_ids = set(
        database.scalars(
            select(AssessmentQuestion.question_id).where(
                AssessmentQuestion.assessment_id
                == assessment.id
            )
        ).all()
    )

    compulsory_question_ids = database.scalars(
        select(Question.id).where(
            Question.is_compulsory.is_(True)
        )
    ).all()

    new_rows = [
        AssessmentQuestion(
            assessment_id=assessment.id,
            question_id=question_id,
            is_active=True,
        )
        for question_id in compulsory_question_ids
        if question_id not in existing_question_ids
    ]

    if new_rows:
        database.add_all(new_rows)


def get_active_assessment_question(
    assessment_id: int,
    question_id: int,
    organisation_id: int,
    database: DatabaseSession,
) -> AssessmentQuestion:
    get_owned_assessment(
        assessment_id,
        organisation_id,
        database,
    )

    assessment_question = database.scalar(
        select(AssessmentQuestion)
        .options(
            selectinload(
                AssessmentQuestion.question
            )
        )
        .where(
            AssessmentQuestion.assessment_id
            == assessment_id,
            AssessmentQuestion.question_id
            == question_id,
            AssessmentQuestion.is_active.is_(True),
        )
    )

    if assessment_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "This question is not active for the "
                "assessment."
            ),
        )

    return assessment_question


@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    assessment_input: AssessmentCreateRequest,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> Assessment:
    highest_existing_number = (
        database.scalar(
            select(
                func.max(
                    Assessment
                    .organisation_assessment_number
                )
            ).where(
                Assessment.organisation_id
                == organisation.id
            )
        )
        or 0
    )

    next_assessment_number = (
        highest_existing_number + 1
    )

    assessment = Assessment(
        organisation_id=organisation.id,
        organisation_assessment_number=(
            next_assessment_number
        ),
        name=assessment_input.name,
        status="draft",
    )

    database.add(assessment)
    database.flush()

    initialise_compulsory_questions(
        assessment,
        database,
    )

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
            Assessment.organisation_id
            == organisation.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
    )

    return list(
        database.scalars(statement).all()
    )


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
)
def get_assessment(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> Assessment:
    return get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

@router.get(
    "/{assessment_id}/report",
    response_class=Response,
)
def download_assessment_report(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> Response:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    if assessment.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Complete the assessment before "
                "downloading the report."
            ),
        )

    analysis = database.scalar(
        select(AIAnalysis).where(
            AIAnalysis.assessment_id
            == assessment.id,
        )
    )

    pdf_bytes = generate_assessment_report(
        assessment=assessment,
        organisation=organisation,
        analysis=analysis,
        database=database,
    )

    safe_filename = (
        f"safeplus-assessment-"
        f"{assessment.organisation_assessment_number}"
        f".pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_filename}"'
            ),
        },
    )

@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assessment(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> None:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    database.delete(assessment)
    database.commit()


@router.get(
    "/{assessment_id}/questions",
    response_model=list[
        AssessmentQuestionSetupResponse
    ],
)
def get_assessment_questions(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> list[AssessmentQuestionSetupResponse]:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    initialise_compulsory_questions(
        assessment,
        database,
    )

    database.commit()

    active_question_ids = set(
        database.scalars(
            select(
                AssessmentQuestion.question_id
            ).where(
                AssessmentQuestion.assessment_id
                == assessment.id,
                AssessmentQuestion.is_active.is_(
                    True
                ),
            )
        ).all()
    )

    rows = database.execute(
        select(Question, Domain)
        .join(
            Domain,
            Question.domain_id == Domain.id,
        )
        .options(
            selectinload(Question.domain)
        )
        .order_by(
            Domain.display_order,
            Question.id,
        )
    ).all()

    return [
        AssessmentQuestionSetupResponse(
            question_id=question.id,
            question_number=(
                question.question_number
            ),
            domain_name=domain.name,
            employee_text=question.employee_text,
            manager_text=question.manager_text,
            is_compulsory=(
                question.is_compulsory
            ),
            is_situation_dependent=(
                question.is_situation_dependent
            ),
            is_active=(
                question.id
                in active_question_ids
            ),
        )
        for question, domain in rows
    ]


@router.put(
    "/{assessment_id}/question-selection",
    response_model=list[
        AssessmentQuestionSetupResponse
    ],
)
def update_situation_question_selection(
    assessment_id: int,
    selection: SituationQuestionSelectionRequest,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> list[AssessmentQuestionSetupResponse]:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    ensure_assessment_is_editable(
        assessment
    )

    initialise_compulsory_questions(
        assessment,
        database,
    )

    valid_situation_ids = set(
        database.scalars(
            select(Question.id).where(
                Question.is_situation_dependent.is_(
                    True
                )
            )
        ).all()
    )

    requested_ids = set(
        selection.question_ids
    )

    invalid_ids = (
        requested_ids - valid_situation_ids
    )

    if invalid_ids:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "One or more selected questions "
                "are invalid."
            ),
        )

    database.execute(
        delete(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id
            == assessment.id,
            AssessmentQuestion.question_id.in_(
                valid_situation_ids
            ),
        )
    )

    database.add_all(
        [
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=question_id,
                is_active=True,
            )
            for question_id in requested_ids
        ]
    )

    database.commit()

    return get_assessment_questions(
        assessment_id,
        organisation,
        database,
    )


@router.put(
    (
        "/{assessment_id}/questions/"
        "{question_id}/responses"
    ),
    response_model=QuestionResponsesResponse,
)
def update_question_responses(
    assessment_id: int,
    question_id: int,
    response_update: QuestionResponsesUpdate,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> QuestionResponsesResponse:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    ensure_assessment_is_editable(
        assessment
    )

    assessment_question = (
        get_active_assessment_question(
            assessment_id,
            question_id,
            organisation.id,
            database,
        )
    )

    received_options = [
        response.response_option
        for response
        in response_update.responses
    ]

    if len(received_options) != len(
        set(received_options)
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Each response option may only "
                "appear once."
            ),
        )

    na_count = next(
        (
            response.count
            for response
            in response_update.responses
            if response.response_option
            == "N/A"
        ),
        0,
    )

    if na_count > 0:
        question = (
            assessment_question.question
        )

        if (
            response_update.respondent_group
            != "Employee"
            or not (
                question.is_situation_dependent
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "N/A is only allowed for "
                    "Employee responses to "
                    "situation-dependent questions."
                ),
            )

    database.execute(
        delete(ResponseCount).where(
            ResponseCount.assessment_question_id
            == assessment_question.id,
            ResponseCount.respondent_group
            == response_update.respondent_group,
        )
    )

    response_rows = [
        ResponseCount(
            assessment_question_id=(
                assessment_question.id
            ),
            respondent_group=(
                response_update.respondent_group
            ),
            response_option=(
                response.response_option
            ),
            count=response.count,
        )
        for response
        in response_update.responses
        if response.count > 0
    ]

    database.add_all(response_rows)

    if (
        response_rows
        and assessment.status == "draft"
    ):
        assessment.status = "in_progress"

    database.commit()

    return QuestionResponsesResponse(
        assessment_id=assessment.id,
        question_id=question_id,
        respondent_group=(
            response_update.respondent_group
        ),
        responses=[
            ResponseCountResponse(
                response_option=(
                    row.response_option
                ),
                count=row.count,
            )
            for row in response_rows
        ],
    )


@router.get(
    (
        "/{assessment_id}/questions/"
        "{question_id}/responses/"
        "{respondent_group}"
    ),
    response_model=QuestionResponsesResponse,
)
def get_question_responses(
    assessment_id: int,
    question_id: int,
    respondent_group: str,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> QuestionResponsesResponse:
    if respondent_group not in {
        "Employee",
        "Senior Manager",
    }:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid respondent group.",
        )

    assessment_question = (
        get_active_assessment_question(
            assessment_id,
            question_id,
            organisation.id,
            database,
        )
    )

    response_rows = list(
        database.scalars(
            select(ResponseCount)
            .where(
                ResponseCount.assessment_question_id
                == assessment_question.id,
                ResponseCount.respondent_group
                == respondent_group,
            )
            .order_by(ResponseCount.id)
        ).all()
    )

    return QuestionResponsesResponse(
        assessment_id=assessment_id,
        question_id=question_id,
        respondent_group=respondent_group,
        responses=[
            ResponseCountResponse.model_validate(
                row
            )
            for row in response_rows
        ],
    )


@router.post(
    "/{assessment_id}/calculate-scores",
    response_model=AssessmentScoringResponse,
)
def calculate_scores(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> AssessmentScoringResponse:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    scoring_result = (
        calculate_assessment_scores(
            assessment,
            database,
        )
    )

    return (
        AssessmentScoringResponse.model_validate(
            scoring_result
        )
    )


@router.post(
    "/{assessment_id}/complete",
    response_model=AssessmentCompletionResponse,
)
def complete_assessment(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> AssessmentCompletionResponse:
    assessment = get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    if assessment.status == "completed":
        if (
            assessment.completed_at is None
            or (
                assessment.overall_combined_mean
                is None
            )
            or (
                assessment.overall_maturity_label
                is None
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "This assessment is marked as "
                    "completed but its final results "
                    "are incomplete."
                ),
            )

        question_score_count = (
            database.scalar(
                select(
                    func.count(
                        QuestionScore.id
                    )
                )
                .join(
                    AssessmentQuestion,
                    (
                        QuestionScore
                        .assessment_question_id
                        == AssessmentQuestion.id
                    ),
                )
                .where(
                    AssessmentQuestion.assessment_id
                    == assessment.id
                )
            )
        )

        return AssessmentCompletionResponse(
            assessment_id=assessment.id,
            status=assessment.status,
            completed_at=(
                assessment.completed_at
            ),
            overall_combined_mean=(
                assessment
                .overall_combined_mean
            ),
            overall_maturity_label=(
                assessment
                .overall_maturity_label
            ),
            questions_scored=(
                question_score_count or 0
            ),
        )

    active_questions = list(
        database.execute(
            select(
                AssessmentQuestion,
                Question,
            )
            .join(
                Question,
                (
                    AssessmentQuestion.question_id
                    == Question.id
                ),
            )
            .where(
                AssessmentQuestion.assessment_id
                == assessment.id,
                AssessmentQuestion.is_active.is_(
                    True
                ),
            )
            .order_by(Question.id)
        ).all()
    )

    if not active_questions:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "This assessment has no active "
                "questions."
            ),
        )

    incomplete_questions: list[
        IncompleteQuestionResponse
    ] = []

    for (
        assessment_question,
        question,
    ) in active_questions:
        response_groups = set(
            database.scalars(
                select(
                    ResponseCount.respondent_group
                ).where(
                    ResponseCount
                    .assessment_question_id
                    == assessment_question.id,
                    ResponseCount.count > 0,
                    ResponseCount.response_option
                    != "N/A",
                )
            ).all()
        )

        missing_groups = [
            respondent_group
            for respondent_group in (
                "Employee",
                "Senior Manager",
            )
            if respondent_group
            not in response_groups
        ]

        if missing_groups:
            incomplete_questions.append(
                IncompleteQuestionResponse(
                    question_id=question.id,
                    question_number=(
                        question.question_number
                    ),
                    missing_groups=(
                        missing_groups
                    ),
                )
            )

    if incomplete_questions:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail={
                "message": (
                    "All active questions require "
                    "Employee and Senior Manager "
                    "responses."
                ),
                "incomplete_questions": [
                    item.model_dump()
                    for item
                    in incomplete_questions
                ],
            },
        )

    scoring_result = (
        calculate_assessment_scores(
            assessment,
            database,
        )
    )

    if (
        assessment.overall_combined_mean
        is None
        or (
            assessment.overall_maturity_label
            is None
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "An overall result could not be "
                "calculated. Each of the three "
                "domains must contain at least one "
                "scored question."
            ),
        )

    assessment.status = "completed"
    assessment.completed_at = datetime.now(
        timezone.utc
    )

    database.commit()
    database.refresh(assessment)

    return AssessmentCompletionResponse(
        assessment_id=assessment.id,
        status=assessment.status,
        completed_at=assessment.completed_at,
        overall_combined_mean=(
            assessment.overall_combined_mean
        ),
        overall_maturity_label=(
            assessment.overall_maturity_label
        ),
        questions_scored=int(
            scoring_result[
                "questions_scored"
            ]
        ),
    )