from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class GeneratedDomainSummary(BaseModel):
    domain_name: str = Field(
        min_length=1,
        max_length=100,
    )

    score: float = Field(
        ge=1.0,
        le=5.0,
    )

    maturity_level: str = Field(
        min_length=1,
        max_length=30,
    )

    summary: str = Field(
        min_length=1,
        max_length=1200,
    )

    strengths: list[str] = Field(
        default_factory=list,
        max_length=5,
    )

    improvement_areas: list[str] = Field(
        default_factory=list,
        max_length=5,
    )

    source_ids: list[str] = Field(
        min_length=1,
        max_length=5,
    )


class GeneratedPriorityActionNarrative(BaseModel):
    """AI narrative for a single rule-selected priority action.

    Selection, ranking, and urgency are decided entirely by the
    rule engine (see app/services/priority_actions.py) per FR14/
    FR15 and the Scoring and Maturity Framework V1 (section 6.4:
    "The tier is a deterministic input to the AI, not an AI
    output"). The AI supplies only the narrative fields below for
    each question_id it is given — it must not invent, drop, or
    reorder candidates.
    """

    question_id: int

    reason: str = Field(
        min_length=1,
        max_length=800,
    )

    recommended_action: str = Field(
        min_length=1,
        max_length=1200,
    )

    source_ids: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    source_relevance: str = Field(
        min_length=1,
        max_length=800,
    )


class GeneratedRoadmapItem(BaseModel):
    timeframe: str = Field(
        min_length=1,
        max_length=100,
    )

    objective: str = Field(
        min_length=1,
        max_length=300,
    )

    actions: list[str] = Field(
        min_length=1,
        max_length=6,
    )

    success_indicator: str = Field(
        min_length=1,
        max_length=500,
    )

    source_ids: list[str] = Field(
        min_length=1,
        max_length=5,
    )


class GeneratedAIAnalysis(BaseModel):
    overall_summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    key_strengths: list[str] = Field(
        min_length=1,
        max_length=6,
    )

    key_risks: list[str] = Field(
        min_length=1,
        max_length=6,
    )

    domain_summaries: list[
        GeneratedDomainSummary
    ] = Field(
        min_length=1,
        max_length=3,
    )

    priority_actions: list[
        GeneratedPriorityActionNarrative
    ] = Field(
        default_factory=list,
        max_length=5,
    )

    roadmap: list[
        GeneratedRoadmapItem
    ] = Field(
        min_length=1,
        max_length=6,
    )

    limitations: list[str] = Field(
        min_length=1,
        max_length=5,
    )


class AIAnalysisResponse(BaseModel):
    id: int
    assessment_id: int
    overall_summary: str | None

    domain_summaries: (
        dict[str, object] | None
    )

    priority_actions: (
        list[dict[str, object]] | None
    )

    roadmap: (
        list[dict[str, object]] | None
    )

    ai_provider: str
    generated_at: datetime | None
    status: str
    included_in_report: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class AIAnalysisInclusionRequest(BaseModel):
    included_in_report: bool


class AIAnalysisGenerationResponse(
    AIAnalysisResponse
):
    message: str