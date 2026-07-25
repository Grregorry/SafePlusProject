from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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