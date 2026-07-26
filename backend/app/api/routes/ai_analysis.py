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
)
from app.core.config import settings
from app.data.safeplus_guidance import (
    SAFEPLUS_GUIDANCE_SOURCES,
)
from app.models import (
    AIAnalysis,
    Assessment,
)
from app.schemas.ai_analysis import (
    AIAnalysisGenerationResponse,
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


def get_owned_assessment(
    assessment_id: int,
    organisation_id: int,
    database: DatabaseSession,
) -> Assessment:
    assessment = database.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.organisation_id
            == organisation_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    return assessment


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

    database.commit()
    database.refresh(analysis)

    try:
        generated = generate_gemini_analysis(
            assessment,
            database,
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

        analysis.priority_actions = [
            item.model_dump(
                mode="json"
            )
            for item
            in generated.priority_actions
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