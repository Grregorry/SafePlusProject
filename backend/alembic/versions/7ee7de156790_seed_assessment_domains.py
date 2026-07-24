"""seed assessment domains

Revision ID: 7ee7de156790
Revises: f20797e2587e
Create Date: 2026-07-25 01:36:45.565668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

domain_table = sa.table(
    "domain",
    sa.column("name", sa.String(length=100)),
    sa.column("display_order", sa.SmallInteger()),
)

# revision identifiers, used by Alembic.
revision: str = '7ee7de156790'
down_revision: Union[str, Sequence[str], None] = 'f20797e2587e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.bulk_insert(
        domain_table,
        [
            {
                "name": "Leadership",
                "display_order": 1,
            },
            {
                "name": "Worker Engagement",
                "display_order": 2,
            },
            {
                "name": "Risk Management",
                "display_order": 3,
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        domain_table.delete().where(
            domain_table.c.name.in_(
                [
                    "Leadership",
                    "Worker Engagement",
                    "Risk Management",
                ]
            )
        )
    )
