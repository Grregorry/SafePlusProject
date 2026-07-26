from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
)
from app.models import (
    Assessment,
    AssessmentQuestion,
    Domain,
    IndividualResponse,
    Organisation,
    Question,
    SurveySubmission,
)
from app.schemas.public_survey import (
    CreateSurveySubmissionRequest,
    CreateSurveySubmissionResponse,
    PublicSurveyOverviewResponse,
    PublicSurveyQuestionResponse,
    SaveSurveyAnswerRequest,
    SaveSurveyAnswerResponse,
    SubmitSurveyResponse,
    SurveyAccessResponse,
    SurveySubmissionDetailResponse,
)


router = APIRouter(
    tags=["public surveys"],
)


def get_public_assessment(
    public_code: str,
    database: DatabaseSession,
) -> Assessment:
    assessment = database.scalar(
        select(Assessment).where(
            Assessment.public_code == public_code.upper(),
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found.",
        )

    return assessment


def get_submission(
    submission_token: str,
    database: DatabaseSession,
) -> SurveySubmission:
    submission = database.scalar(
        select(SurveySubmission).where(
            SurveySubmission.access_token == submission_token,
        )
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey submission not found.",
        )

    return submission


def get_active_question_rows(
    assessment_id: int,
    database: DatabaseSession,
) -> list[tuple[AssessmentQuestion, Question, Domain]]:
    return list(
        database.execute(
            select(
                AssessmentQuestion,
                Question,
                Domain,
            )
            .join(
                Question,
                AssessmentQuestion.question_id == Question.id,
            )
            .join(
                Domain,
                Question.domain_id == Domain.id,
            )
            .where(
                AssessmentQuestion.assessment_id == assessment_id,
                AssessmentQuestion.is_active.is_(True),
            )
            .order_by(
                Domain.display_order,
                Question.id,
            )
        ).all()
    )


@router.get(
    "/api/assessments/{assessment_id}/survey-access",
    response_model=SurveyAccessResponse,
)
def get_survey_access(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> SurveyAccessResponse:
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

    return SurveyAccessResponse(
        assessment_id=assessment.id,
        public_code=assessment.public_code,
        public_path=f"/survey/{assessment.public_code}",
        status=assessment.status,
    )


@router.get(
    "/api/public/surveys/{public_code}",
    response_model=PublicSurveyOverviewResponse,
)
def get_public_survey(
    public_code: str,
    database: DatabaseSession,
) -> PublicSurveyOverviewResponse:
    assessment = get_public_assessment(
        public_code,
        database,
    )

    if assessment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This survey is closed.",
        )

    organisation_name = database.scalar(
        select(Organisation.name).where(
            Organisation.id == assessment.organisation_id,
        )
    )

    active_question_count = len(
        get_active_question_rows(
            assessment.id,
            database,
        )
    )

    return PublicSurveyOverviewResponse(
        public_code=assessment.public_code,
        organisation_name=organisation_name or "Organisation",
        assessment_status=assessment.status,
        active_question_count=active_question_count,
    )


@router.post(
    "/api/public/surveys/{public_code}/submissions",
    response_model=CreateSurveySubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_public_submission(
    public_code: str,
    request: CreateSurveySubmissionRequest,
    database: DatabaseSession,
) -> CreateSurveySubmissionResponse:
    assessment = get_public_assessment(
        public_code,
        database,
    )

    if assessment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This survey is closed.",
        )

    active_questions = get_active_question_rows(
        assessment.id,
        database,
    )

    if not active_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This survey has no active questions.",
        )

    submission = SurveySubmission(
        assessment_id=assessment.id,
        respondent_group=request.respondent_group,
        status="in_progress",
    )

    database.add(submission)

    if assessment.status == "draft":
        assessment.status = "in_progress"

    database.commit()
    database.refresh(submission)

    return CreateSurveySubmissionResponse(
        submission_token=submission.access_token,
        respondent_group=submission.respondent_group,
        status=submission.status,
        started_at=submission.started_at,
    )


@router.get(
    "/api/public/submissions/{submission_token}",
    response_model=SurveySubmissionDetailResponse,
)
def get_public_submission(
    submission_token: str,
    database: DatabaseSession,
) -> SurveySubmissionDetailResponse:
    submission = get_submission(
        submission_token,
        database,
    )

    assessment = database.get(
        Assessment,
        submission.assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    organisation_name = database.scalar(
        select(Organisation.name).where(
            Organisation.id == assessment.organisation_id,
        )
    )

    question_rows = get_active_question_rows(
        assessment.id,
        database,
    )

    saved_responses = list(
        database.scalars(
            select(IndividualResponse).where(
                IndividualResponse.submission_id == submission.id,
            )
        ).all()
    )

    responses_by_question = {
        response.assessment_question_id: response.response_option
        for response in saved_responses
    }

    questions = [
        PublicSurveyQuestionResponse(
            question_id=question.id,
            question_number=question.question_number,
            domain_name=domain.name,
            question_text=(
                question.employee_text
                if submission.respondent_group == "Employee"
                else question.manager_text
            ),
            is_situation_dependent=question.is_situation_dependent,
            selected_response=responses_by_question.get(
                assessment_question.id
            ),
        )
        for assessment_question, question, domain in question_rows
    ]

    return SurveySubmissionDetailResponse(
        submission_token=submission.access_token,
        public_code=assessment.public_code,
        organisation_name=organisation_name or "Organisation",
        respondent_group=submission.respondent_group,
        status=submission.status,
        started_at=submission.started_at,
        submitted_at=submission.submitted_at,
        answered_question_count=len(saved_responses),
        total_question_count=len(question_rows),
        questions=questions,
    )


@router.put(
    "/api/public/submissions/{submission_token}/answers",
    response_model=SaveSurveyAnswerResponse,
)
def save_public_answer(
    submission_token: str,
    request: SaveSurveyAnswerRequest,
    database: DatabaseSession,
) -> SaveSurveyAnswerResponse:
    submission = get_submission(
        submission_token,
        database,
    )

    if submission.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Submitted surveys cannot be edited.",
        )

    assessment_question = database.scalar(
        select(AssessmentQuestion)
        .join(
            Question,
            AssessmentQuestion.question_id == Question.id,
        )
        .where(
            AssessmentQuestion.assessment_id
            == submission.assessment_id,
            AssessmentQuestion.question_id
            == request.question_id,
            AssessmentQuestion.is_active.is_(True),
        )
    )

    if assessment_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question is not active for this survey.",
        )

    question = database.get(
        Question,
        request.question_id,
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found.",
        )

    if request.response_option == "N/A":
        if (
            submission.respondent_group != "Employee"
            or not question.is_situation_dependent
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "N/A is only allowed for Employee responses "
                    "to situation-dependent questions."
                ),
            )

    existing_response = database.scalar(
        select(IndividualResponse).where(
            IndividualResponse.submission_id == submission.id,
            IndividualResponse.assessment_question_id
            == assessment_question.id,
        )
    )

    if existing_response is None:
        existing_response = IndividualResponse(
            submission_id=submission.id,
            assessment_question_id=assessment_question.id,
            response_option=request.response_option,
        )

        database.add(existing_response)

    else:
        existing_response.response_option = request.response_option

    database.commit()

    answered_question_count = len(
        database.scalars(
            select(IndividualResponse.id).where(
                IndividualResponse.submission_id == submission.id,
            )
        ).all()
    )

    total_question_count = len(
        get_active_question_rows(
            submission.assessment_id,
            database,
        )
    )

    return SaveSurveyAnswerResponse(
        question_id=request.question_id,
        response_option=request.response_option,
        answered_question_count=answered_question_count,
        total_question_count=total_question_count,
    )


@router.post(
    "/api/public/submissions/{submission_token}/submit",
    response_model=SubmitSurveyResponse,
)
def submit_public_survey(
    submission_token: str,
    database: DatabaseSession,
) -> SubmitSurveyResponse:
    submission = get_submission(
        submission_token,
        database,
    )

    question_rows = get_active_question_rows(
        submission.assessment_id,
        database,
    )

    total_question_count = len(question_rows)

    answered_question_count = len(
        database.scalars(
            select(IndividualResponse.id).where(
                IndividualResponse.submission_id == submission.id,
            )
        ).all()
    )

    if answered_question_count != total_question_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"All questions must be answered before submission. "
                f"{answered_question_count} of "
                f"{total_question_count} questions are answered."
            ),
        )

    if submission.status != "submitted":
        submission.status = "submitted"
        submission.submitted_at = datetime.now(
            timezone.utc
        )

        database.commit()
        database.refresh(submission)

    if submission.submitted_at is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Submission completion time is unavailable.",
        )

    return SubmitSurveyResponse(
        submission_token=submission.access_token,
        status=submission.status,
        submitted_at=submission.submitted_at,
        answered_question_count=answered_question_count,
        total_question_count=total_question_count,
    )