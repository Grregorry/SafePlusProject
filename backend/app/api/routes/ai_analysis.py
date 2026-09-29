from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy import select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
    get_owned_assessment,
)
from app.core.config import settings
from app.data.safeplus_guidance import (
    SAFEPLUS_GUIDANCE_SOURCES,
)
from app.models import AIAnalysis
from app.schemas.ai_analysis import (
    AIAnalysisGenerationResponse,
    AIAnalysisInclusionRequest,
    AIAnalysisResponse,
)
from app.services.gemini_analysis import (
    GeminiAnalysisError,
    generate_gemini_analysis,
)


router = APIRouter(
    prefix="/api/assessments",
    tags=["ai-analysis"],
)


def build_analysis_response(
    analysis: AIAnalysis,
) -> AIAnalysisResponse:
    return AIAnalysisResponse(
        id=analysis.id,
        assessment_id=analysis.assessment_id,
        overall_summary=(
            analysis.overall_summary
        ),
        domain_summaries=(
            analysis.domain_summaries
        ),
        priority_actions=(
            analysis.priority_actions
        ),
        roadmap=analysis.roadmap,
        ai_provider=analysis.ai_provider,
        generated_at=analysis.generated_at,
        status=analysis.status,
        included_in_report=(
            analysis.included_in_report
        ),
    )


@router.get(
    "/{assessment_id}/ai-analysis",
    response_model=AIAnalysisResponse,
)
def get_ai_analysis(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> AIAnalysisResponse:
    get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    analysis = database.scalar(
        select(AIAnalysis).where(
            AIAnalysis.assessment_id
            == assessment_id,
        )
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "AI analysis has not been generated "
                "for this assessment."
            ),
        )

    return build_analysis_response(
        analysis
    )


@router.get(
    "/ai-analysis/sources",
)
def get_ai_analysis_sources(
    organisation: CurrentOrganisation,
) -> dict[str, object]:
    return {
        "sources": SAFEPLUS_GUIDANCE_SOURCES,
        "count": len(
            SAFEPLUS_GUIDANCE_SOURCES
        ),
        "notice": (
            "These curated WorkSafe SafePlus "
            "sources are used to ground AI "
            "recommendations."
        ),
    }


@router.put(
    "/{assessment_id}/ai-analysis/inclusion",
    response_model=AIAnalysisResponse,
)
def update_ai_analysis_inclusion(
    assessment_id: int,
    payload: AIAnalysisInclusionRequest,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> AIAnalysisResponse:
    get_owned_assessment(
        assessment_id,
        organisation.id,
        database,
    )

    analysis = database.scalar(
        select(AIAnalysis).where(
            AIAnalysis.assessment_id
            == assessment_id,
        )
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "AI analysis has not been generated "
                "for this assessment."
            ),
        )

    if (
        payload.included_in_report
        and analysis.status != "completed"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only a completed AI analysis can be "
                "included in the report."
            ),
        )

    analysis.included_in_report = (
        payload.included_in_report
    )

    database.commit()
    database.refresh(analysis)

    return build_analysis_response(
        analysis
    )


@router.post(
    "/{assessment_id}/ai-analysis/generate",
    response_model=AIAnalysisGenerationResponse,
)
def generate_ai_analysis(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
) -> AIAnalysisGenerationResponse:
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
                "generating AI analysis."
            ),
        )

    analysis = database.scalar(
        select(AIAnalysis).where(
            AIAnalysis.assessment_id
            == assessment.id,
        )
    )

    provider_name = (
        f"Google Gemini "
        f"({settings.gemini_model})"
    )

    if analysis is None:
        analysis = AIAnalysis(
            assessment_id=assessment.id,
            ai_provider=provider_name,
            status="pending",
        )

        database.add(analysis)
    else:
        analysis.status = "pending"
        analysis.ai_provider = provider_name
        # New wording has not been checked by anyone yet.
        analysis.included_in_report = False

    database.commit()
    database.refresh(analysis)

    try:
        generated, priority_action_candidates = (
            generate_gemini_analysis(
                assessment,
                database,
            )
        )

        analysis.overall_summary = (
            generated.overall_summary
        )

        analysis.domain_summaries = {
            "key_strengths": (
                generated.key_strengths
            ),
            "key_risks": (
                generated.key_risks
            ),
            "domains": [
                item.model_dump(
                    mode="json"
                )
                for item in (
                    generated.domain_summaries
                )
            ],
            "limitations": (
                generated.limitations
            ),
            "guidance_sources": (
                SAFEPLUS_GUIDANCE_SOURCES
            ),
        }

        narratives_by_question_id = {
            item.question_id: item
            for item
            in generated.priority_actions
        }

        analysis.priority_actions = [
            {
                **candidate,
                **narratives_by_question_id[
                    candidate["question_id"]
                ].model_dump(
                    mode="json",
                    exclude={"question_id"},
                ),
            }
            for candidate
            in priority_action_candidates
        ]

        analysis.roadmap = [
            item.model_dump(
                mode="json"
            )
            for item in generated.roadmap
        ]

        analysis.generated_at = datetime.now(
            timezone.utc
        )

        analysis.status = "completed"

        database.commit()
        database.refresh(analysis)

        return AIAnalysisGenerationResponse(
            **build_analysis_response(
                analysis
            ).model_dump(),
            message=(
                "AI analysis generated successfully "
                "using curated WorkSafe SafePlus "
                "guidance."
            ),
        )

    except GeminiAnalysisError as error:
        analysis.status = "failed"

        database.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=str(error),
        ) from error

    except Exception as error:
        analysis.status = "failed"

        database.commit()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "An unexpected error occurred while "
                "generating AI analysis."
            ),
        ) from error