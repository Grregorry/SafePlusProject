from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class AssessmentCreateRequest(
    BaseModel
):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:
        cleaned_name = " ".join(
            value.split()
        )

        if not cleaned_name:
            raise ValueError(
                (
                    "Assessment name cannot "
                    "be empty."
                )
            )

        return cleaned_name


class AssessmentQuestionSetupResponse(
    BaseModel
):
    question_id: int
    question_number: str
    domain_name: str
    employee_text: str
    manager_text: str
    is_compulsory: bool
    is_situation_dependent: bool
    is_active: bool


class SituationQuestionSelectionRequest(
    BaseModel
):
    question_ids: list[int] = Field(
        default_factory=list
    )


class AssessmentResponse(BaseModel):
    id: int
    organisation_id: int
    organisation_assessment_number: int
    name: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    overall_combined_mean: (
        Decimal | None
    )
    overall_maturity_label: (
        str | None
    )
    expected_manual_entries_employee: int
    expected_manual_entries_manager: int

    model_config = ConfigDict(
        from_attributes=True,
    )

    @model_validator(mode="after")
    def hide_scores_until_completed(
        self,
    ) -> "AssessmentResponse":
        # A partial score for an open assessment can reveal how the
        # latest respondent answered, so it is never sent.
        if self.status != "completed":
            self.overall_combined_mean = None
            self.overall_maturity_label = None

        return self


class ExpectedManualEntriesUpdate(
    BaseModel
):
    expected_manual_entries_employee: int = Field(
        ge=0,
    )
    expected_manual_entries_manager: int = Field(
        ge=0,
    )


class ResponseCountInput(BaseModel):
    response_option: Literal[
        "Strongly Agree",
        "Agree",
        "Neither Agree nor Disagree",
        "Disagree",
        "Strongly Disagree",
        "N/A",
    ]

    count: int = Field(
        ge=0,
    )


class QuestionResponsesUpdate(
    BaseModel
):
    respondent_group: Literal[
        "Employee",
        "Senior Manager",
    ]

    responses: list[
        ResponseCountInput
    ]


class ResponseCountResponse(
    BaseModel
):
    response_option: str
    count: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class QuestionResponsesResponse(
    BaseModel
):
    assessment_id: int
    question_id: int
    respondent_group: str
    responses: list[
        ResponseCountResponse
    ]


class QuestionScoreResponse(
    BaseModel
):
    question_id: int
    question_number: str
    employee_mean: Decimal
    manager_mean: Decimal
    combined_mean: Decimal
    opinion_gap: Decimal
    maturity_level: str
    intervention_tier: str


class DomainScoreResponse(BaseModel):
    domain_id: int
    combined_mean: Decimal
    maturity_level: str


class AssessmentScoringResponse(
    BaseModel
):
    assessment_id: int
    questions_scored: int
    question_scores: list[
        QuestionScoreResponse
    ]
    domain_scores: list[
        DomainScoreResponse
    ]
    overall_combined_mean: (
        Decimal | None
    )
    overall_maturity_label: (
        str | None
    )


class IncompleteQuestionResponse(
    BaseModel
):
    question_id: int
    question_number: str
    missing_groups: list[str]


class AssessmentCompletionResponse(
    BaseModel
):
    assessment_id: int
    status: str
    completed_at: datetime
    overall_combined_mean: Decimal
    overall_maturity_label: str
    questions_scored: int