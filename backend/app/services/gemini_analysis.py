from __future__ import annotations

import json
import logging
from decimal import Decimal

from google import genai
from google.genai import types
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.data.safeplus_guidance import (
    SAFEPLUS_AI_LIMITATIONS,
    SAFEPLUS_GUIDANCE_SOURCES,
)
from app.models import (
    Assessment,
    AssessmentQuestion,
    Domain,
    DomainScore,
    Organisation,
    Question,
)
from app.models.question_score import (
    QuestionScore,
)
from app.schemas.ai_analysis import (
    GeneratedAIAnalysis,
)
from app.services.priority_actions import (
    select_priority_action_candidates,
)


logger = logging.getLogger(__name__)


class GeminiAnalysisError(Exception):
    """Raised when SafePlus AI analysis cannot be generated."""


def decimal_to_float(
    value: Decimal | None,
) -> float | None:
    if value is None:
        return None

    return float(value)


def build_assessment_data(
    assessment: Assessment,
    database: Session,
) -> dict[str, object]:
    organisation = database.scalar(
        select(Organisation).where(
            Organisation.id
            == assessment.organisation_id
        )
    )

    if organisation is None:
        raise GeminiAnalysisError(
            (
                "The organisation linked to "
                "this assessment could not "
                "be found."
            )
        )

    domain_rows = database.execute(
        select(
            Domain,
            DomainScore,
        )
        .join(
            DomainScore,
            DomainScore.domain_id
            == Domain.id,
        )
        .where(
            DomainScore.assessment_id
            == assessment.id,
        )
        .order_by(
            Domain.display_order,
        )
    ).all()

    question_rows = database.execute(
        select(
            AssessmentQuestion,
            Question,
            Domain,
            QuestionScore,
        )
        .join(
            Question,
            AssessmentQuestion.question_id
            == Question.id,
        )
        .join(
            Domain,
            Question.domain_id
            == Domain.id,
        )
        .join(
            QuestionScore,
            QuestionScore.assessment_question_id
            == AssessmentQuestion.id,
        )
        .where(
            AssessmentQuestion.assessment_id
            == assessment.id,
            AssessmentQuestion.is_active.is_(
                True
            ),
        )
        .order_by(
            Domain.display_order,
            Question.id,
        )
    ).all()

    domains = [
        {
            "domain_id": domain.id,
            "domain_name": domain.name,
            "combined_mean": decimal_to_float(
                domain_score.combined_mean
            ),
            "maturity_level": (
                domain_score.maturity_level
            ),
        }
        for domain, domain_score
        in domain_rows
    ]

    questions = [
        {
            "question_id": question.id,
            "question_number": (
                question.question_number
            ),
            "domain_name": domain.name,
            "employee_wording": (
                question.employee_text
            ),
            "manager_wording": (
                question.manager_text
            ),
            "employee_mean": decimal_to_float(
                question_score.employee_mean
            ),
            "manager_mean": decimal_to_float(
                question_score.manager_mean
            ),
            "combined_mean": decimal_to_float(
                question_score.combined_mean
            ),
            "opinion_gap": decimal_to_float(
                question_score.opinion_gap
            ),
            "maturity_level": (
                question_score.maturity_level
            ),
            "intervention_tier": (
                question_score.intervention_tier
            ),
        }
        for (
            _assessment_question,
            question,
            domain,
            question_score,
        ) in question_rows
    ]

    return {
        "assessment_id": assessment.id,
        "assessment_name": assessment.name,
        "organisation": {
            "name": organisation.name,
            "category": organisation.category,
        },
        "overall_combined_mean": (
            decimal_to_float(
                assessment.overall_combined_mean
            )
        ),
        "overall_maturity_label": (
            assessment.overall_maturity_label
        ),
        "domains": domains,
        "questions": questions,
        "priority_action_candidates": (
            select_priority_action_candidates(
                questions
            )
        ),
    }


def build_guidance_data() -> dict[str, object]:
    return {
        "approved_sources": (
            SAFEPLUS_GUIDANCE_SOURCES
        ),
        "required_limitations": (
            SAFEPLUS_AI_LIMITATIONS
        ),
    }


def build_analysis_prompt(
    assessment_data: dict[str, object],
) -> str:
    organisation_data = (
        assessment_data.get(
            "organisation",
            {},
        )
    )

    organisation_category = "Other"

    if isinstance(
        organisation_data,
        dict,
    ):
        category_value = (
            organisation_data.get(
                "category"
            )
        )

        if isinstance(
            category_value,
            str,
        ):
            organisation_category = (
                category_value
            )

    assessment_json = json.dumps(
        assessment_data,
        indent=2,
        ensure_ascii=False,
    )

    guidance_json = json.dumps(
        build_guidance_data(),
        indent=2,
        ensure_ascii=False,
    )

    return f"""
You are generating a SafePlus workplace health and safety
self-assessment analysis for an organisation.

Organisation category:

{organisation_category}

Use the organisation category to make the wording, examples,
risk priorities, and recommended actions more relevant to the
organisation's sector, but only where this is supported by the
supplied assessment evidence and approved WorkSafe guidance.

Do not invent sector-specific incidents, hazards, legal duties,
regulations, compliance findings, worker statements, or
organisation details.

You must use only:

1. The supplied SafePlus assessment data.
2. The supplied curated guidance summaries from official
   WorkSafe New Zealand SafePlus sources.

Do not use unsupported external facts.

SafePlus scoring scale:

- 1.00 to 2.49 = Developing
- 2.50 to 3.99 = Performing
- 4.00 to 5.00 = Leading

Interpretation rules:

- Lower combined scores indicate greater need for improvement.
- High and Medium intervention tiers require additional
  attention.
- Large Employee and Senior Manager opinion gaps indicate
  different perceptions that should be explored.
- Recommendations should support continuous improvement.
- The existence of a policy or document alone does not prove
  that health and safety practice is effective.

Required analysis behaviour:

1. Base every conclusion on supplied assessment evidence.
2. Clearly identify strengths and risks.
3. Give priority to:
   - Developing scores,
   - High intervention tiers,
   - Medium intervention tiers,
   - low domain scores,
   - large opinion gaps.
4. Use constructive and professional language.
5. Recommend practical actions suitable for workplace
   managers and health and safety teams.
6. Tailor recommendations to the organisation category where
   supported by the supplied assessment evidence and approved
   WorkSafe guidance.
7. Do not invent workplace incidents, legal breaches,
   policies, worker statements, or organisation details.
8. Do not provide legal advice.
9. Do not state that the organisation is legally compliant
   or non-compliant.
10. Do not claim that this analysis replaces a qualified
    SafePlus assessor.
11. Every domain summary and roadmap item must include valid
    source IDs from the supplied official source list.
12. Use practical roadmap timeframes such as:
    - Immediate or 0 to 30 days
    - Short term or 1 to 3 months
    - Medium term or 3 to 6 months
    - Longer term or 6 to 12 months
13. Include the supplied AI limitations in the limitations
    section, using clear wording.
14. Return all required fields in the structured response.

Priority actions — selection is already decided for you:

The list under "priority_action_candidates" below has already
been selected and ranked by the rule engine (highest to lowest
leverage: High tier questions first, then Medium, then Low,
ranked within each tier by Combined mean ascending and Opinion
Gap descending). This ranking and the "urgency" tier are fixed
inputs, not something you calculate.

Do not add, remove, re-rank, or re-tier these candidates. For
"priority_actions" in your response, return exactly one
narrative object per candidate in "priority_action_candidates",
matched by its "question_id", each containing only: "reason"
(why this matters, referencing the supplied evidence),
"recommended_action" (a practical, specific action), "source_ids"
(valid IDs from the approved source list), and
"source_relevance" (why those sources apply). If
"priority_action_candidates" is empty, return an empty
"priority_actions" list.

Assessment data:

{assessment_json}

Approved WorkSafe SafePlus guidance:

{guidance_json}
""".strip()


def validate_source_ids(
    generated: GeneratedAIAnalysis,
) -> None:
    valid_source_ids = {
        str(source["source_id"])
        for source
        in SAFEPLUS_GUIDANCE_SOURCES
    }

    referenced_source_ids: list[str] = []

    for domain_summary in (
        generated.domain_summaries
    ):
        referenced_source_ids.extend(
            domain_summary.source_ids
        )

    for priority_action in (
        generated.priority_actions
    ):
        referenced_source_ids.extend(
            priority_action.source_ids
        )

    for roadmap_item in generated.roadmap:
        referenced_source_ids.extend(
            roadmap_item.source_ids
        )

    invalid_source_ids = sorted(
        {
            source_id
            for source_id
            in referenced_source_ids
            if source_id
            not in valid_source_ids
        }
    )

    if invalid_source_ids:
        invalid_values = ", ".join(
            invalid_source_ids
        )

        raise GeminiAnalysisError(
            (
                "Gemini referenced unsupported "
                "SafePlus sources: "
                f"{invalid_values}."
            )
        )


def validate_priority_action_question_ids(
    generated: GeneratedAIAnalysis,
    candidates: list[dict[str, object]],
) -> None:
    expected_question_ids = {
        candidate["question_id"]
        for candidate in candidates
    }

    returned_question_ids = [
        priority_action.question_id
        for priority_action
        in generated.priority_actions
    ]

    if len(returned_question_ids) != len(
        set(returned_question_ids)
    ):
        raise GeminiAnalysisError(
            (
                "Gemini returned duplicate "
                "priority action question IDs."
            )
        )

    if set(returned_question_ids) != (
        expected_question_ids
    ):
        raise GeminiAnalysisError(
            (
                "Gemini's priority actions did "
                "not match the rule-engine's "
                "selected candidates."
            )
        )


def generate_gemini_analysis(
    assessment: Assessment,
    database: Session,
) -> tuple[
    GeneratedAIAnalysis,
    list[dict[str, object]],
]:
    if not settings.gemini_api_key:
        raise GeminiAnalysisError(
            (
                "GEMINI_API_KEY is not "
                "configured."
            )
        )

    if (
        assessment.overall_combined_mean
        is None
        or assessment.overall_maturity_label
        is None
    ):
        raise GeminiAnalysisError(
            (
                "Assessment scores must be "
                "calculated before AI analysis "
                "can be generated."
            )
        )

    assessment_data = (
        build_assessment_data(
            assessment,
            database,
        )
    )

    domains = assessment_data.get(
        "domains",
    )

    questions = assessment_data.get(
        "questions",
    )

    if (
        not isinstance(domains, list)
        or not domains
    ):
        raise GeminiAnalysisError(
            (
                "No domain scores are "
                "available for this "
                "assessment."
            )
        )

    if (
        not isinstance(questions, list)
        or not questions
    ):
        raise GeminiAnalysisError(
            (
                "No question scores are "
                "available for this "
                "assessment."
            )
        )

    priority_action_candidates = (
        assessment_data.get(
            "priority_action_candidates",
        )
    )

    if not isinstance(
        priority_action_candidates,
        list,
    ):
        priority_action_candidates = []

    client = genai.Client(
        api_key=settings.gemini_api_key,
    )

    try:
        response = (
            client.models.generate_content(
                model=settings.gemini_model,
                contents=(
                    build_analysis_prompt(
                        assessment_data
                    )
                ),
                config=(
                    types
                    .GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=(
                            GeneratedAIAnalysis
                        ),
                    )
                ),
            )
        )
    except Exception as error:
        logger.exception(
            "Gemini analysis request failed"
        )

        # Google reports overload (503) and rate or quota limits (429)
        # with a status code; say so plainly instead of the generic hint.
        status_code = getattr(error, "code", None)

        if status_code == 503:
            raise GeminiAnalysisError(
                (
                    "Gemini is busy right now because "
                    "of high demand. Please wait a few "
                    "minutes and try again."
                )
            ) from error

        if status_code == 429:
            raise GeminiAnalysisError(
                (
                    "Gemini's usage limit has been "
                    "reached. Wait a minute and try "
                    "again, or check the API quota."
                )
            ) from error

        raise GeminiAnalysisError(
            (
                "Gemini could not generate "
                "the analysis. Check the API "
                "key, model access, quota, "
                "and internet connection, "
                "then try again."
            )
        ) from error

    if not response.text:
        raise GeminiAnalysisError(
            (
                "Gemini returned an empty "
                "response."
            )
        )

    try:
        generated = (
            GeneratedAIAnalysis
            .model_validate_json(
                response.text
            )
        )
    except ValidationError as error:
        logger.exception(
            (
                "Gemini returned invalid "
                "structured data"
            )
        )

        raise GeminiAnalysisError(
            (
                "Gemini returned an invalid "
                "analysis format. Please "
                "try again."
            )
        ) from error

    validate_source_ids(generated)

    validate_priority_action_question_ids(
        generated,
        priority_action_candidates,
    )

    return generated, priority_action_candidates