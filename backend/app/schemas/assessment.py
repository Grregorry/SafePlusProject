from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field



class AssessmentQuestionSetupResponse(BaseModel):
    question_id: int
    question_number: str
    domain_name: str
    employee_text: str
    manager_text: str
    is_compulsory: bool
    is_situation_dependent: bool
    is_active: bool


class SituationQuestionSelectionRequest(BaseModel):
    question_ids: list[int] = Field(default_factory=list)

class AssessmentResponse(BaseModel):
    id: int
    organisation_id: int
    status: str
    created_at: datetime
    completed_at: datetime | None
    overall_combined_mean: Decimal | None
    overall_maturity_label: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )