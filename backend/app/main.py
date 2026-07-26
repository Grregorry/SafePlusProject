import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.assessment_progress import (
    router as assessment_progress_router,
)
from app.api.routes.assessments import (
    router as assessments_router,
)
from app.api.routes.auth import router as auth_router
from app.api.routes.public_surveys import (
    router as public_surveys_router,
)
from app.api.routes.questions import (
    router as questions_router,
)
from app.db.session import engine


logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafePlus API",
    description=(
        "Backend API for the SafePlus assessment platform."
    ),
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(questions_router)
app.include_router(assessments_router)
app.include_router(assessment_progress_router)
app.include_router(public_surveys_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "SafePlus API is running",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get("/database/health")
def database_health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception as error:
        logger.exception(
            "Database connection failed"
        )

        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        ) from error