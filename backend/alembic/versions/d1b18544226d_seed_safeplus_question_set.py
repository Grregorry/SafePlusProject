"""seed SafePlus question set

Revision ID: d1b18544226d
Revises: 7ee7de156790
Create Date: 2026-07-25 14:07:59.242007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b18544226d'
down_revision: Union[str, Sequence[str], None] = '7ee7de156790'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert the complete SafePlus question set."""

    connection = op.get_bind()

    domain_rows = connection.execute(
        sa.text(
            """
            SELECT id, name
            FROM domain
            WHERE name IN (
                'Leadership',
                'Worker Engagement',
                'Risk Management'
            )
            """
        )
    ).fetchall()

    domain_ids = {
        row.name: row.id
        for row in domain_rows
    }

    required_domains = {
        "Leadership",
        "Worker Engagement",
        "Risk Management",
    }

    missing_domains = required_domains - set(domain_ids)

    if missing_domains:
        raise RuntimeError(
            f"Cannot seed questions. Missing domains: {sorted(missing_domains)}"
        )

    question_table = sa.table(
        "question",
        sa.column("domain_id", sa.Integer()),
        sa.column("question_number", sa.String(length=10)),
        sa.column("employee_text", sa.Text()),
        sa.column("manager_text", sa.Text()),
        sa.column("is_compulsory", sa.Boolean()),
        sa.column("is_situation_dependent", sa.Boolean()),
    )

    questions = [
        # Domain 1: Leadership
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.1",
            "employee_text": (
                "My organisation has a clear strategy in place to deal with "
                "risks to my safety."
            ),
            "manager_text": (
                "We have a clear strategy in place to deal with risks to "
                "worker safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.2",
            "employee_text": (
                "My organisation has a clear strategy in place to deal with "
                "risks to my health in my place of work."
            ),
            "manager_text": (
                "We have a clear strategy in place to deal with risks to "
                "worker health in their workplace."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.3",
            "employee_text": (
                "My organisation considers both health and safety before "
                "making changes that affect me."
            ),
            "manager_text": (
                "I think about impacts on both health and safety when I "
                "make decisions."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.4",
            "employee_text": (
                "I'm given the time, support and right gear to look after "
                "my safety."
            ),
            "manager_text": (
                "I make sure enough resources (including people, time, money "
                "and support) are available to ensure worker safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.5",
            "employee_text": (
                "I'm given the time, support and right gear to look after "
                "my health at work."
            ),
            "manager_text": (
                "I make sure resources (including people, time, money and "
                "support) are available to ensure worker health at work."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.6",
            "employee_text": (
                "I'm involved in checking how successfully the organisation "
                "manages risk and wider health and safety."
            ),
            "manager_text": (
                "We have a process for workers and their representatives to "
                "be involved in checking how successfully the organisation "
                "manages risk and wider health and safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.7",
            "employee_text": (
                "I'm given the resources (for example, training, coaching, "
                "feedback, equipment and support) I need to be competent "
                "and work safely."
            ),
            "manager_text": (
                "I make sure resources (for example, for training, coaching, "
                "feedback, equipment and support) are available so workers "
                "are competent and have what they need to work safely."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.8",
            "employee_text": (
                "I'm not worried about raising health and safety concerns or "
                "having honest conversations about health and safety."
            ),
            "manager_text": (
                "Because of the decisions I make and the actions I take, "
                "workers aren't worried about having honest conversations "
                "about health and safety, or raising health and safety "
                "concerns with me."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.9",
            "employee_text": (
                "My organisation's actions show it's committed to my health "
                "and safety."
            ),
            "manager_text": (
                "The decisions I make and the actions I take prove I'm "
                "committed to health and safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.10",
            "employee_text": (
                "If I'm physically or mentally unwell, I'll be given "
                "alternative/restricted duties."
            ),
            "manager_text": (
                "I make sure time and resources are available so workers who "
                "are physically or mentally unwell can carry out "
                "alternative/restricted duties."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.11",
            "employee_text": (
                "My organisation is always looking for ways to improve my "
                "health and safety."
            ),
            "manager_text": (
                "We have an active process for improving health and safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Leadership"],
            "question_number": "1.12",
            "employee_text": (
                "The contractors I work with are competent and have what "
                "they need to work safely."
            ),
            "manager_text": (
                "I make sure resources are available to make sure contractors "
                "are competent and have what they need to work safely."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },

        # Domain 2: Worker Engagement
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.1",
            "employee_text": (
                "My organisation talks to me about health and safety in a "
                "way I can understand."
            ),
            "manager_text": (
                "I talk with workers about health and safety in a way they "
                "can understand."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.2",
            "employee_text": (
                "I'm involved in deciding how health and safety risks will "
                "be dealt with."
            ),
            "manager_text": (
                "We involve workers and their representatives in deciding "
                "how health and safety risks will be dealt with."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.3",
            "employee_text": (
                "If I'm in danger or someone else is, I have the authority "
                "to take steps."
            ),
            "manager_text": (
                "Workers are encouraged to act if they're in danger or "
                "someone else is."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.4",
            "employee_text": (
                "My organisation listens to my ideas and feedback on health "
                "and safety."
            ),
            "manager_text": (
                "We receive and consider workers' feedback and ideas on "
                "health and safety matters."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.5",
            "employee_text": (
                "I can get involved and have my say about health and safety."
            ),
            "manager_text": (
                "We have an agreed process for workers to get involved and "
                "have their say about health and safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.6",
            "employee_text": (
                "My organisation is good at sorting out health and safety "
                "disagreements/concerns."
            ),
            "manager_text": (
                "We have a good process for sorting out health and safety "
                "disagreements/concerns."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Worker Engagement"],
            "question_number": "2.7",
            "employee_text": (
                "I have the time, support, and training to be involved in "
                "health and safety."
            ),
            "manager_text": (
                "I make sure we have the time, resources and processes to "
                "encourage and support workers and their representatives to "
                "be involved in health and safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },

        # Domain 3: Risk Management
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.1",
            "employee_text": (
                "The organisation identifies the risks to my safety."
            ),
            "manager_text": (
                "We identify the risks to worker safety."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.2",
            "employee_text": (
                "I know the organisation identifies the risks to my health "
                "in the workplace."
            ),
            "manager_text": (
                "We identify the risks to worker health in the workplace."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.3",
            "employee_text": (
                "I always speak up and report health and safety risks and "
                "incidents."
            ),
            "manager_text": (
                "Workers always speak up and report health and safety risks "
                "and incidents."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.4",
            "employee_text": (
                "The organisation assesses the risks to my health and safety."
            ),
            "manager_text": (
                "We assess health and safety risks."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.5",
            "employee_text": (
                "The organisation has taken actions to reduce risk (control "
                "measures) for work that could cause me serious harm."
            ),
            "manager_text": (
                "We have taken actions to reduce risk (control measures) for "
                "work that could cause serious harm."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.6",
            "employee_text": (
                "The organisation regularly checks that the actions it takes "
                "to reduce risk (control measures) are still keeping me "
                "healthy and safe."
            ),
            "manager_text": (
                "We regularly check that the actions we take to reduce risk "
                "(control measures) are still keeping workers and others "
                "healthy and safe."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.7",
            "employee_text": (
                "My organisation investigates health and safety incidents "
                "and makes changes to how I do things as a result."
            ),
            "manager_text": (
                "We have procedures to investigate each health and safety "
                "incident, and changes are made to reduce the chances of it "
                "happening again."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.8",
            "employee_text": (
                "My organisation is prepared for emergencies and has told "
                "me what to do when one happens."
            ),
            "manager_text": (
                "We have an emergency plan in place that workers know."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.9",
            "employee_text": (
                "My organisation manages the risks to me from manual handling "
                "the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from manual handling the best we "
                "possibly can."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.10",
            "employee_text": (
                "My organisation manages the risks to me from slips, trips "
                "and falls the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from slips, trips and falls the best "
                "we possibly can."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.11",
            "employee_text": (
                "My organisation manages the risks to me from bullying the "
                "best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from bullying the best we possibly can."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.12",
            "employee_text": (
                "My organisation manages the risks to me from fatigue the "
                "best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from fatigue the best we possibly can."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.13",
            "employee_text": (
                "My organisation manages the risks to me from work-related "
                "stress the best it possibly can."
            ),
            "manager_text": (
                "I'm certain the organisation manages the risks from "
                "work-related stress the best it possibly can."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.14",
            "employee_text": (
                "My organisation manages the risks to me from sexual "
                "harassment the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from sexual harassment the best we "
                "possibly can."
            ),
            "is_compulsory": True,
            "is_situation_dependent": False,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.15",
            "employee_text": (
                "My organisation manages the risks to me from noise the best "
                "it possibly can."
            ),
            "manager_text": (
                "We manage the risks from noise the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.16",
            "employee_text": (
                "My organisation manages the risks to me from dust the best "
                "it possibly can."
            ),
            "manager_text": (
                "We manage the risks from dust the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.17",
            "employee_text": (
                "My organisation manages the risks to me from hazardous "
                "substances the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from hazardous substances the best we "
                "possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.18",
            "employee_text": (
                "My organisation manages the risks to me from vibration the "
                "best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from vibration the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.19",
            "employee_text": (
                "My organisation manages the risks to me from violence the "
                "best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from violence the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.20",
            "employee_text": (
                "My organisation manages the risks to me from driving the "
                "best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from driving the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.21",
            "employee_text": (
                "My organisation manages the risks to me from working with "
                "machinery the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from working with machinery the best "
                "we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.22",
            "employee_text": (
                "My organisation manages the risks from solar UV radiation "
                "the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from solar UV radiation the best we "
                "possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.23",
            "employee_text": (
                "My organisation manages the risks to me from hazardous "
                "energy the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from hazardous energy the best we "
                "possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.24",
            "employee_text": (
                "My organisation manages the risks to me from working at "
                "height the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from working at height the best we "
                "possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.25",
            "employee_text": (
                "My organisation manages the risks to me from working in "
                "confined spaces the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from working in confined spaces the best "
                "we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.26",
            "employee_text": (
                "My organisation manages the risks to me from mobile plant "
                "the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from mobile plant the best we possibly "
                "can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.27",
            "employee_text": (
                "My organisation manages the risk to me from animals the best "
                "it possibly can."
            ),
            "manager_text": (
                "We manage the risks from animals the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.28",
            "employee_text": (
                "My organisation manages the risks to me from biological "
                "exposures the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from biological exposures the best we "
                "possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.29",
            "employee_text": (
                "My organisation manages the risks to me from working in "
                "temperature extremes the best it possibly can."
            ),
            "manager_text": (
                "We manage the risks from working in temperature extremes "
                "the best we possibly can."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
        {
            "domain_id": domain_ids["Risk Management"],
            "question_number": "3.30",
            "employee_text": (
                "My organisation makes sure my mental health is looked after "
                "when I work from home."
            ),
            "manager_text": (
                "We manage the risks to the mental health of staff who work "
                "from home so far as is reasonably practicable."
            ),
            "is_compulsory": False,
            "is_situation_dependent": True,
        },
    ]

    op.bulk_insert(question_table, questions)


def downgrade() -> None:
    """Remove the seeded SafePlus questions."""

    op.execute(
        sa.text(
            """
            DELETE FROM question
            WHERE question_number IN (
                '1.1', '1.2', '1.3', '1.4', '1.5', '1.6',
                '1.7', '1.8', '1.9', '1.10', '1.11', '1.12',
                '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7',
                '3.1', '3.2', '3.3', '3.4', '3.5', '3.6',
                '3.7', '3.8', '3.9', '3.10', '3.11', '3.12',
                '3.13', '3.14', '3.15', '3.16', '3.17',
                '3.18', '3.19', '3.20', '3.21', '3.22',
                '3.23', '3.24', '3.25', '3.26', '3.27',
                '3.28', '3.29', '3.30'
            )
            """
        )
    )