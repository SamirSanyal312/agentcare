from fastapi import FastAPI

from app.api.routes import admin
from app.api.routes import auth
from app.api.routes import patient
from app.api.routes import staff
from app.config import settings

from app.api.routes import appointments
from app.api.routes import hospital

from app.api.routes import requests

app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic AI for healthcare administration "
        "and care coordination."
    ),
    version="0.2.0",
)


app.include_router(auth.router)
app.include_router(patient.router)
app.include_router(staff.router)
app.include_router(admin.router)

app.include_router(hospital.router)
app.include_router(appointments.router)

app.include_router(requests.router)


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