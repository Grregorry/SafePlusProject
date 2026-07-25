from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
)
from app.models import (
    Assessment,
    AssessmentQuestion,
    Domain,
    Question,
    ResponseCount,
)
from app.schemas.assessment import (
    AssessmentQuestionSetupResponse,
    AssessmentResponse,
    QuestionResponsesResponse,
    QuestionResponsesUpdate,
    ResponseCountResponse,
    SituationQuestionSelectionRequest,
)


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


def initialise_compulsory_questions(
    assessment: Assessment,
    database: DatabaseSession,
) -> None:
    existing_question_ids = set(
        database.scalars(
            select(AssessmentQuestion.question_id).where(
                AssessmentQuestion.assessment_id == assessment.id
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
            Assessment.organisation_id == organisation.id
        )
        .order_by(Assessment.created_at.desc())
    )

    return list(database.scalars(statement).all())


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
    "/{assessment_id}/questions",
    response_model=list[AssessmentQuestionSetupResponse],
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
            select(AssessmentQuestion.question_id).where(
                AssessmentQuestion.assessment_id == assessment.id,
                AssessmentQuestion.is_active.is_(True),
            )
        ).all()
    )

    rows = database.execute(
        select(Question, Domain)
        .join(Domain, Question.domain_id == Domain.id)
        .options(selectinload(Question.domain))
        .order_by(
            Domain.display_order,
            Question.id,
        )
    ).all()

    return [
        AssessmentQuestionSetupResponse(
            question_id=question.id,
            question_number=question.question_number,
            domain_name=domain.name,
            employee_text=question.employee_text,
            manager_text=question.manager_text,
            is_compulsory=question.is_compulsory,
            is_situation_dependent=question.is_situation_dependent,
            is_active=question.id in active_question_ids,
        )
        for question, domain in rows
    ]


@router.put(
    "/{assessment_id}/question-selection",
    response_model=list[AssessmentQuestionSetupResponse],
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

    initialise_compulsory_questions(
        assessment,
        database,
    )

    valid_situation_ids = set(
        database.scalars(
            select(Question.id).where(
                Question.is_situation_dependent.is_(True)
            )
        ).all()
    )

    requested_ids = set(selection.question_ids)

    invalid_ids = requested_ids - valid_situation_ids

    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected questions are invalid.",
        )

    database.execute(
        delete(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id == assessment.id,
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
            selectinload(AssessmentQuestion.question)
        )
        .where(
            AssessmentQuestion.assessment_id == assessment_id,
            AssessmentQuestion.question_id == question_id,
            AssessmentQuestion.is_active.is_(True),
        )
    )

    if assessment_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "This question is not active for the assessment."
            ),
        )

    return assessment_question


@router.put(
    "/{assessment_id}/questions/{question_id}/responses",
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

    assessment_question = get_active_assessment_question(
        assessment_id,
        question_id,
        organisation.id,
        database,
    )

    received_options = [
        response.response_option
        for response in response_update.responses
    ]

    if len(received_options) != len(set(received_options)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each response option may only appear once.",
        )

    na_count = next(
        (
            response.count
            for response in response_update.responses
            if response.response_option == "N/A"
        ),
        0,
    )

    if na_count > 0:
        question = assessment_question.question

        if (
            response_update.respondent_group != "Employee"
            or not question.is_situation_dependent
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "N/A is only allowed for Employee responses "
                    "to situation-dependent questions."
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
            assessment_question_id=assessment_question.id,
            respondent_group=response_update.respondent_group,
            response_option=response.response_option,
            count=response.count,
        )
        for response in response_update.responses
        if response.count > 0
    ]

    database.add_all(response_rows)

    if response_rows and assessment.status == "draft":
        assessment.status = "in_progress"

    database.commit()

    return QuestionResponsesResponse(
        assessment_id=assessment.id,
        question_id=question_id,
        respondent_group=response_update.respondent_group,
        responses=[
            ResponseCountResponse(
                response_option=row.response_option,
                count=row.count,
            )
            for row in response_rows
        ],
    )

@router.get(
    "/{assessment_id}/questions/{question_id}/responses/{respondent_group}",
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid respondent group.",
        )

    assessment_question = get_active_assessment_question(
        assessment_id,
        question_id,
        organisation.id,
        database,
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
            ResponseCountResponse.model_validate(row)
            for row in response_rows
        ],
    )