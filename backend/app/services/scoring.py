from __future__ import annotations

from collections import defaultdict
from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_question import (
    AssessmentQuestion,
)
from app.models.domain_score import DomainScore
from app.models.manual_response_count import (
    ManualResponseCount,
)
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


def round_score(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        TWO_DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    )


def combine_counts_by_option(
    *count_lists: list[ResponseCount]
    | list[ManualResponseCount],
) -> dict[str, int]:
    combined: dict[str, int] = {}

    for count_list in count_lists:
        for response_count in count_list:
            combined[
                response_count.response_option
            ] = (
                combined.get(
                    response_count.response_option,
                    0,
                )
                + response_count.count
            )

    return combined


def calculate_group_mean(
    counts_by_option: dict[str, int],
) -> Decimal | None:
    weighted_total = Decimal("0")
    response_total = 0

    for (
        response_option,
        count,
    ) in counts_by_option.items():
        if response_option == "N/A":
            continue

        score_value = LIKERT_VALUES.get(
            response_option
        )

        if score_value is None:
            continue

        weighted_total += (
            score_value * count
        )

        response_total += count

    if response_total == 0:
        return None

    return round_score(
        weighted_total
        / Decimal(response_total)
    )


def get_maturity_level(
    score: Decimal,
) -> str:
    if score <= Decimal("2.50"):
        return "Developing"

    if score >= Decimal("4.50"):
        return "Leading"

    return "Performing"


def get_intervention_tier(
    combined_mean: Decimal,
    opinion_gap: Decimal,
) -> str:
    if opinion_gap >= Decimal("3.00"):
        return "High"

    if (
        combined_mean
        <= Decimal("2.50")
        and opinion_gap
        > Decimal("1.50")
    ):
        return "High"

    if combined_mean <= Decimal("2.50"):
        return "Medium"

    if (
        combined_mean
        <= Decimal("3.50")
        and opinion_gap
        > Decimal("1.50")
    ):
        return "Medium"

    if combined_mean <= Decimal("3.50"):
        return "Low"

    if (
        combined_mean
        < Decimal("4.50")
        and opinion_gap
        > Decimal("1.50")
    ):
        return "Low"

    return "Not flagged"


def calculate_mean(
    scores: list[Decimal],
) -> Decimal | None:
    if not scores:
        return None

    return round_score(
        sum(
            scores,
            Decimal("0"),
        )
        / Decimal(len(scores))
    )


def calculate_assessment_scores(
    assessment: Assessment,
    database: Session,
) -> dict[str, object]:
    active_assessment_questions = list(
        database.scalars(
            select(
                AssessmentQuestion
            )
            .where(
                AssessmentQuestion.assessment_id
                == assessment.id,
                AssessmentQuestion.is_active.is_(
                    True
                ),
            )
            .order_by(
                AssessmentQuestion.id
            )
        ).all()
    )

    existing_question_scores = list(
        database.scalars(
            select(QuestionScore)
            .join(
                AssessmentQuestion,
                (
                    QuestionScore
                    .assessment_question_id
                    == AssessmentQuestion.id
                ),
            )
            .where(
                AssessmentQuestion.assessment_id
                == assessment.id
            )
        ).all()
    )

    existing_question_score_map = {
        score.assessment_question_id: score
        for score
        in existing_question_scores
    }

    existing_domain_scores = list(
        database.scalars(
            select(DomainScore).where(
                DomainScore.assessment_id
                == assessment.id
            )
        ).all()
    )

    existing_domain_score_map = {
        score.domain_id: score
        for score in existing_domain_scores
    }

    assessment.overall_combined_mean = None
    assessment.overall_maturity_label = None

    question_results: list[
        dict[str, object]
    ] = []

    domain_question_scores: dict[
        int,
        list[Decimal],
    ] = defaultdict(list)

    scored_assessment_question_ids: set[
        int
    ] = set()

    for assessment_question in (
        active_assessment_questions
    ):
        question = database.scalar(
            select(Question).where(
                Question.id
                == assessment_question.question_id
            )
        )

        if question is None:
            continue

        digital_counts = list(
            database.scalars(
                select(ResponseCount).where(
                    ResponseCount
                    .assessment_question_id
                    == assessment_question.id
                )
            ).all()
        )

        manual_counts = list(
            database.scalars(
                select(
                    ManualResponseCount
                ).where(
                    ManualResponseCount
                    .assessment_question_id
                    == assessment_question.id
                )
            ).all()
        )

        employee_counts = combine_counts_by_option(
            [
                count
                for count in digital_counts
                if count.respondent_group
                == "Employee"
            ],
            [
                count
                for count in manual_counts
                if count.respondent_group
                == "Employee"
            ],
        )

        manager_counts = combine_counts_by_option(
            [
                count
                for count in digital_counts
                if count.respondent_group
                == "Senior Manager"
            ],
            [
                count
                for count in manual_counts
                if count.respondent_group
                == "Senior Manager"
            ],
        )

        employee_mean = (
            calculate_group_mean(
                employee_counts
            )
        )

        manager_mean = (
            calculate_group_mean(
                manager_counts
            )
        )

        if (
            employee_mean is None
            or manager_mean is None
        ):
            continue

        combined_mean = round_score(
            (
                employee_mean
                + manager_mean
            )
            / Decimal("2")
        )

        opinion_gap = round_score(
            abs(
                employee_mean
                - manager_mean
            )
        )

        maturity_level = (
            get_maturity_level(
                combined_mean
            )
        )

        intervention_tier = (
            get_intervention_tier(
                combined_mean,
                opinion_gap,
            )
        )

        existing_question_score = (
            existing_question_score_map.get(
                assessment_question.id
            )
        )

        if existing_question_score is None:
            question_score = QuestionScore(
                assessment_question_id=(
                    assessment_question.id
                ),
                employee_mean=employee_mean,
                manager_mean=manager_mean,
                combined_mean=combined_mean,
                opinion_gap=opinion_gap,
                maturity_level=maturity_level,
                intervention_tier=(
                    intervention_tier
                ),
            )

            database.add(
                question_score
            )
        else:
            existing_question_score.employee_mean = (
                employee_mean
            )

            existing_question_score.manager_mean = (
                manager_mean
            )

            existing_question_score.combined_mean = (
                combined_mean
            )

            existing_question_score.opinion_gap = (
                opinion_gap
            )

            existing_question_score.maturity_level = (
                maturity_level
            )

            existing_question_score.intervention_tier = (
                intervention_tier
            )

        scored_assessment_question_ids.add(
            assessment_question.id
        )

        domain_question_scores[
            question.domain_id
        ].append(
            combined_mean
        )

        question_results.append(
            {
                "question_id": (
                    question.id
                ),
                "question_number": (
                    question.question_number
                ),
                "employee_mean": (
                    employee_mean
                ),
                "manager_mean": (
                    manager_mean
                ),
                "combined_mean": (
                    combined_mean
                ),
                "opinion_gap": (
                    opinion_gap
                ),
                "maturity_level": (
                    maturity_level
                ),
                "intervention_tier": (
                    intervention_tier
                ),
            }
        )

    for existing_score in (
        existing_question_scores
    ):
        if (
            existing_score
            .assessment_question_id
            not in (
                scored_assessment_question_ids
            )
        ):
            database.delete(
                existing_score
            )

    domain_results: list[
        dict[str, object]
    ] = []

    calculated_domain_means: list[
        Decimal
    ] = []

    calculated_domain_ids: set[int] = set()

    for (
        domain_id,
        combined_scores,
    ) in domain_question_scores.items():
        domain_mean = calculate_mean(
            combined_scores
        )

        if domain_mean is None:
            continue

        maturity_level = (
            get_maturity_level(
                domain_mean
            )
        )

        existing_domain_score = (
            existing_domain_score_map.get(
                domain_id
            )
        )

        if existing_domain_score is None:
            database.add(
                DomainScore(
                    assessment_id=(
                        assessment.id
                    ),
                    domain_id=domain_id,
                    combined_mean=(
                        domain_mean
                    ),
                    maturity_level=(
                        maturity_level
                    ),
                )
            )
        else:
            existing_domain_score.combined_mean = (
                domain_mean
            )

            existing_domain_score.maturity_level = (
                maturity_level
            )

        calculated_domain_ids.add(
            domain_id
        )

        calculated_domain_means.append(
            domain_mean
        )

        domain_results.append(
            {
                "domain_id": (
                    domain_id
                ),
                "combined_mean": (
                    domain_mean
                ),
                "maturity_level": (
                    maturity_level
                ),
            }
        )

    for existing_domain_score in (
        existing_domain_scores
    ):
        if (
            existing_domain_score.domain_id
            not in calculated_domain_ids
        ):
            database.delete(
                existing_domain_score
            )

    if len(
        calculated_domain_means
    ) == 3:
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
    database.refresh(
        assessment
    )

    return {
        "assessment_id": (
            assessment.id
        ),
        "questions_scored": len(
            question_results
        ),
        "question_scores": (
            question_results
        ),
        "domain_scores": (
            domain_results
        ),
        "overall_combined_mean": (
            assessment
            .overall_combined_mean
        ),
        "overall_maturity_label": (
            assessment
            .overall_maturity_label
        ),
    }