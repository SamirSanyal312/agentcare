from fastapi import APIRouter
from fastapi import Depends

from app.dependencies import DbSession
from app.dependencies import get_current_patient_profile
from app.models import PatientProfile
from app.schemas.auth import PatientProfileResponse


router = APIRouter(
    prefix="/api/patient",
    tags=["Patient"],
)


@router.get(
    "/profile",
    response_model=PatientProfileResponse,
)
def get_my_patient_profile(
    profile: PatientProfile = Depends(
        get_current_patient_profile
    ),
) -> PatientProfile:
    return profile