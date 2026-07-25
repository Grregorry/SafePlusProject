from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Domain
from app.schemas.question import DomainQuestionsResponse


router = APIRouter(
    prefix="/api/questions",
    tags=["questions"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[DomainQuestionsResponse],
)
def get_questions(
    database: DatabaseSession,
) -> list[Domain]:
    statement = (
        select(Domain)
        .options(selectinload(Domain.questions))
        .order_by(Domain.display_order)
    )

    domains = list(database.scalars(statement).unique().all())

    for domain in domains:
        domain.questions.sort(
            key=lambda question: tuple(
                int(part)
                for part in question.question_number.split(".")
            )
        )

    return domains