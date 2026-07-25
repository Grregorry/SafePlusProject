from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_question import AssessmentQuestion
from app.models.domain_score import DomainScore
from app.models.question import Question
from app.models.question_score import QuestionScore
from app.models.response_count import ResponseCount


LIKERT_VALUES: dict[str, Decimal] = {
    "Strongly Agree": Decimal("5"),
    "Agree": Decimal("4"),
    "Neither Agree nor Disagree": Decimal("3"),
    "Disagree": Decimal("2"),
    "Strongly Disagree": Decimal("1"),
}

TWO_DECIMAL_PLACES = Decimal("0.01")


def round_score(value: Decimal) -> Decimal:
    return value.quantize(
        TWO_DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    )


def calculate_group_mean(
    response_counts: list[ResponseCount],
) -> Decimal | None:
    weighted_total = Decimal("0")
    response_total = 0

    for response_count in response_counts:
        if response_count.response_option == "N/A":
            continue

        score_value = LIKERT_VALUES.get(
            response_count.response_option
        )

        if score_value is None:
            continue

        weighted_total += (
            score_value * response_count.count
        )

        response_total += response_count.count

    if response_total == 0:
        return None

    return round_score(
        weighted_total / Decimal(response_total)
    )


def get_maturity_level(score: Decimal) -> str:
    if score <= Decimal("2.50"):
        return "Developing"

    if score >= Decimal("4.50"):
        return "Leading"

    return "Performing"


def get_intervention_tier(
    combined_mean: Decimal,
    opinion_gap: Decimal,
) -> str:
    # Extreme opinion-gap override.
    if opinion_gap >= Decimal("3.00"):
        return "High"

    if (
        combined_mean <= Decimal("2.50")
        and opinion_gap > Decimal("1.50")
    ):
        return "High"

    if combined_mean <= Decimal("2.50"):
        return "Medium"

    if (
        combined_mean <= Decimal("3.50")
        and opinion_gap > Decimal("1.50")
    ):
        return "Medium"

    if combined_mean <= Decimal("3.50"):
        return "Low"

    if (
        combined_mean < Decimal("4.50")
        and opinion_gap > Decimal("1.50")
    ):
        return "Low"

    return "Not flagged"


def calculate_mean(
    scores: list[Decimal],
) -> Decimal | None:
    if not scores:
        return None

    return round_score(
        sum(scores, Decimal("0"))
        / Decimal(len(scores))
    )


def calculate_assessment_scores(
    assessment: Assessment,
    database: Session,
) -> dict[str, object]:
    active_assessment_questions = list(
        database.scalars(
            select(AssessmentQuestion)
            .where(
                AssessmentQuestion.assessment_id
                == assessment.id,
                AssessmentQuestion.is_active.is_(True),
            )
            .order_by(AssessmentQuestion.id)
        ).all()
    )

    assessment_question_ids = [
        assessment_question.id
        for assessment_question
        in active_assessment_questions
    ]

    database.execute(
        delete(QuestionScore).where(
            QuestionScore.assessment_question_id.in_(
                assessment_question_ids
            )
        )
    )

    database.execute(
        delete(DomainScore).where(
            DomainScore.assessment_id == assessment.id
        )
    )

    assessment.overall_combined_mean = None
    assessment.overall_maturity_label = None

    question_results: list[dict[str, object]] = []

    domain_question_scores: dict[
        int,
        list[Decimal],
    ] = defaultdict(list)

    for assessment_question in active_assessment_questions:
        question = database.scalar(
            select(Question).where(
                Question.id
                == assessment_question.question_id
            )
        )

        if question is None:
            continue

        response_counts = list(
            database.scalars(
                select(ResponseCount).where(
                    ResponseCount.assessment_question_id
                    == assessment_question.id
                )
            ).all()
        )

        employee_counts = [
            response_count
            for response_count in response_counts
            if response_count.respondent_group == "Employee"
        ]

        manager_counts = [
            response_count
            for response_count in response_counts
            if response_count.respondent_group
            == "Senior Manager"
        ]

        employee_mean = calculate_group_mean(
            employee_counts
        )

        manager_mean = calculate_group_mean(
            manager_counts
        )

        # Both groups are required for a combined score.
        if employee_mean is None or manager_mean is None:
            continue

        combined_mean = round_score(
            (employee_mean + manager_mean)
            / Decimal("2")
        )

        opinion_gap = round_score(
            abs(employee_mean - manager_mean)
        )

        maturity_level = get_maturity_level(
            combined_mean
        )

        intervention_tier = get_intervention_tier(
            combined_mean,
            opinion_gap,
        )

        question_score = QuestionScore(
            assessment_question_id=assessment_question.id,
            employee_mean=employee_mean,
            manager_mean=manager_mean,
            combined_mean=combined_mean,
            opinion_gap=opinion_gap,
            maturity_level=maturity_level,
            intervention_tier=intervention_tier,
        )

        database.add(question_score)

        domain_question_scores[
            question.domain_id
        ].append(combined_mean)

        question_results.append(
            {
                "question_id": question.id,
                "question_number": question.question_number,
                "employee_mean": employee_mean,
                "manager_mean": manager_mean,
                "combined_mean": combined_mean,
                "opinion_gap": opinion_gap,
                "maturity_level": maturity_level,
                "intervention_tier": intervention_tier,
            }
        )

    domain_results: list[dict[str, object]] = []
    calculated_domain_means: list[Decimal] = []

    for domain_id, combined_scores in (
        domain_question_scores.items()
    ):
        domain_mean = calculate_mean(
            combined_scores
        )

        if domain_mean is None:
            continue

        maturity_level = get_maturity_level(
            domain_mean
        )

        database.add(
            DomainScore(
                assessment_id=assessment.id,
                domain_id=domain_id,
                combined_mean=domain_mean,
                maturity_level=maturity_level,
            )
        )

        calculated_domain_means.append(
            domain_mean
        )

        domain_results.append(
            {
                "domain_id": domain_id,
                "combined_mean": domain_mean,
                "maturity_level": maturity_level,
            }
        )

    # The overall score requires all three domains and gives
    # each domain equal weight.
    if len(calculated_domain_means) == 3:
        overall_mean = calculate_mean(
            calculated_domain_means
        )

        if overall_mean is not None:
            assessment.overall_combined_mean = (
                overall_mean
            )

            assessment.overall_maturity_label = (
                get_maturity_level(
                    overall_mean
                )
            )

    database.commit()
    database.refresh(assessment)

    return {
        "assessment_id": assessment.id,
        "questions_scored": len(question_results),
        "question_scores": question_results,
        "domain_scores": domain_results,
        "overall_combined_mean": (
            assessment.overall_combined_mean
        ),
        "overall_maturity_label": (
            assessment.overall_maturity_label
        ),
    }