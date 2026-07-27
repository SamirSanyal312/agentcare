from fastapi import FastAPI

from app.config import settings


app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic AI for healthcare administration "
        "and care coordination."
    ),
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }