from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import select

from app.api.dependencies import (
    CurrentOrganisation,
    DatabaseSession,
    get_owned_assessment,
)
from app.models import (
    AIAnalysis,
    Assessment,
)
from app.services.assessment_report import (
    generate_assessment_report,
    generate_board_report,
    generate_business_leader_report,
    generate_operational_manager_report,
)


router = APIRouter(
    prefix="/api/assessments",
    tags=["assessments"],
)


@router.get(
    "/{assessment_id}/report",
    response_class=Response,
)
def download_assessment_report(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
    include_ai: bool = False,
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

    analysis = _included_analysis(
        database.scalar(
            select(AIAnalysis).where(
                AIAnalysis.assessment_id
                == assessment.id,
            )
        ),
        include_ai,
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
        f"{'-with-ai' if include_ai else ''}"
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


def _included_analysis(
    analysis: AIAnalysis | None,
    include_ai: bool,
) -> AIAnalysis | None:
    # AI text only goes into a report when the person downloading it
    # chooses to include it.
    if (
        not include_ai
        or analysis is None
        or analysis.status != "completed"
    ):
        return None

    return analysis


def _load_completed_assessment_for_report(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
    include_ai: bool,
) -> tuple[Assessment, AIAnalysis | None]:
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

    analysis = _included_analysis(
        database.scalar(
            select(AIAnalysis).where(
                AIAnalysis.assessment_id
                == assessment.id,
            )
        ),
        include_ai,
    )

    return assessment, analysis


@router.get(
    "/{assessment_id}/report/business-leader",
    response_class=Response,
)
def download_business_leader_report(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
    include_ai: bool = False,
) -> Response:
    assessment, analysis = (
        _load_completed_assessment_for_report(
            assessment_id,
            organisation,
            database,
            include_ai,
        )
    )

    pdf_bytes = generate_business_leader_report(
        assessment=assessment,
        organisation=organisation,
        analysis=analysis,
        database=database,
    )

    safe_filename = (
        f"safeplus-business-leader-report-"
        f"{assessment.organisation_assessment_number}"
        f"{'-with-ai' if include_ai else ''}"
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


@router.get(
    "/{assessment_id}/report/board",
    response_class=Response,
)
def download_board_report(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
    include_ai: bool = False,
) -> Response:
    assessment, analysis = (
        _load_completed_assessment_for_report(
            assessment_id,
            organisation,
            database,
            include_ai,
        )
    )

    pdf_bytes = generate_board_report(
        assessment=assessment,
        organisation=organisation,
        analysis=analysis,
        database=database,
    )

    safe_filename = (
        f"safeplus-board-report-"
        f"{assessment.organisation_assessment_number}"
        f"{'-with-ai' if include_ai else ''}"
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


@router.get(
    "/{assessment_id}/report/operational-manager",
    response_class=Response,
)
def download_operational_manager_report(
    assessment_id: int,
    organisation: CurrentOrganisation,
    database: DatabaseSession,
    include_ai: bool = False,
) -> Response:
    assessment, analysis = (
        _load_completed_assessment_for_report(
            assessment_id,
            organisation,
            database,
            include_ai,
        )
    )

    pdf_bytes = generate_operational_manager_report(
        assessment=assessment,
        organisation=organisation,
        analysis=analysis,
        database=database,
    )

    safe_filename = (
        f"safeplus-operational-manager-report-"
        f"{assessment.organisation_assessment_number}"
        f"{'-with-ai' if include_ai else ''}"
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
