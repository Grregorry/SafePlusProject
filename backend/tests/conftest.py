"""Shared test setup.

Tests run against a separate ``safeplus_test`` database on the same
PostgreSQL server, so the real SafePlusProject data is never touched.
Every test starts from an empty database (the seeded domains and
question set stay in place).

Each test records its input, expected result and actual result with
the ``evidence`` fixture, so a failure report shows what was compared.
"""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE = "safeplus_test"

# Point the app at the test database before anything imports settings.
_base_url = (
    os.environ.get("DATABASE_URL")
    or dotenv_values(BACKEND_DIR / ".env")["DATABASE_URL"]
)
os.environ["DATABASE_URL"] = (
    make_url(_base_url)
    .set(database=TEST_DATABASE)
    .render_as_string(hide_password=False)
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

assert engine.url.database == TEST_DATABASE, "tests must not use the real database"


def _prepare_test_database() -> None:
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )

    with admin.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE},
        ).scalar()

        if not exists:
            connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE}"'))

    admin.dispose()

    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def prepared_database():
    _prepare_test_database()
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(prepared_database):
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE organisation RESTART IDENTITY CASCADE")
        )
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def evidence(record_property):
    """Record a value for the test log, e.g. evidence("actual", ...)."""

    return record_property
