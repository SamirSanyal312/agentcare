from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.dependencies import CurrentUser
from app.dependencies import DbSession
from app.dependencies import get_current_patient_profile
from app.models import PatientProfile
from app.schemas.appointment import (
    AppointmentCreateRequest,
)
from app.schemas.appointment import (
    AppointmentResponse,
)
from app.schemas.appointment import (
    RescheduleAppointmentRequest,
)
from app.services.appointment_exceptions import (
    AppointmentAccessDeniedError,
)
from app.services.appointment_exceptions import (
    AppointmentNotFoundError,
)
from app.services.appointment_exceptions import (
    InvalidAppointmentStateError,
)
from app.services.appointment_exceptions import (
    SlotNotFoundError,
)
from app.services.appointment_exceptions import (
    SlotUnavailableError,
)
from app.services.appointment_service import (
    book_appointment,
)
from app.services.appointment_service import (
    cancel_appointment,
)
from app.services.appointment_service import (
    get_patient_appointment,
)
from app.services.appointment_service import (
    list_patient_appointments,
)
from app.services.appointment_service import (
    reschedule_appointment,
)


router = APIRouter(
    prefix="/api/appointments",
    tags=["Appointments"],
)


def patient_profile_dependency(
    profile: PatientProfile = Depends(
        get_current_patient_profile
    ),
) -> PatientProfile:
    return profile


@router.get(
    "",
    response_model=list[AppointmentResponse],
)
def get_my_appointments(
    db: DbSession,
    patient: PatientProfile = Depends(
        patient_profile_dependency
    ),
):
    return list_patient_appointments(
        db,
        patient,
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    appointment_id: int,
    db: DbSession,
    patient: PatientProfile = Depends(
        patient_profile_dependency
    ),
):
    try:
        return get_patient_appointment(
            db,
            patient,
            appointment_id,
        )

    except AppointmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AppointmentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    request: AppointmentCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
    patient: PatientProfile = Depends(
        patient_profile_dependency
    ),
):
    try:
        return book_appointment(
            db=db,
            patient=patient,
            slot_id=request.slot_id,
            reason=request.reason,
            actor_id=current_user.id,
        )

    except SlotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except SlotUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_my_appointment(
    appointment_id: int,
    current_user: CurrentUser,
    db: DbSession,
    patient: PatientProfile = Depends(
        patient_profile_dependency
    ),
):
    try:
        return cancel_appointment(
            db=db,
            patient=patient,
            appointment_id=appointment_id,
            actor_id=current_user.id,
        )

    except AppointmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AppointmentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except InvalidAppointmentStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{appointment_id}/reschedule",
    response_model=AppointmentResponse,
)
def reschedule_my_appointment(
    appointment_id: int,
    request: RescheduleAppointmentRequest,
    current_user: CurrentUser,
    db: DbSession,
    patient: PatientProfile = Depends(
        patient_profile_dependency
    ),
):
    try:
        return reschedule_appointment(
            db=db,
            patient=patient,
            appointment_id=appointment_id,
            new_slot_id=request.new_slot_id,
            actor_id=current_user.id,
        )

    except AppointmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except AppointmentAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except SlotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except (
        SlotUnavailableError,
        InvalidAppointmentStateError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


