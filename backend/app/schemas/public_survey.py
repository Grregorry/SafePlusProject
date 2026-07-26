from datetime import datetime
from typing import Literal

from pydantic import BaseModel


RespondentGroup = Literal[
    "Employee",
    "Senior Manager",
]

ResponseOption = Literal[
    "Strongly Agree",
    "Agree",
    "Neither Agree nor Disagree",
    "Disagree",
    "Strongly Disagree",
    "N/A",
]


class SurveyAccessResponse(BaseModel):
    assessment_id: int
    public_code: str
    public_path: str
    status: str


class PublicSurveyOverviewResponse(BaseModel):
    public_code: str
    organisation_name: str
    assessment_status: str
    active_question_count: int


class CreateSurveySubmissionRequest(BaseModel):
    respondent_group: RespondentGroup


class CreateSurveySubmissionResponse(BaseModel):
    submission_token: str
    respondent_group: RespondentGroup
    status: str
    started_at: datetime


class PublicSurveyQuestionResponse(BaseModel):
    question_id: int
    question_number: str
    domain_name: str
    question_text: str
    is_situation_dependent: bool
    selected_response: str | None


class SurveySubmissionDetailResponse(BaseModel):
    submission_token: str
    public_code: str
    organisation_name: str
    respondent_group: RespondentGroup
    status: str
    started_at: datetime
    submitted_at: datetime | None
    answered_question_count: int
    total_question_count: int
    questions: list[PublicSurveyQuestionResponse]


class SaveSurveyAnswerRequest(BaseModel):
    question_id: int
    response_option: ResponseOption


class SaveSurveyAnswerResponse(BaseModel):
    question_id: int
    response_option: ResponseOption
    answered_question_count: int
    total_question_count: int


class SubmitSurveyResponse(BaseModel):
    submission_token: str
    status: str
    submitted_at: datetime
    answered_question_count: int
    total_question_count: int