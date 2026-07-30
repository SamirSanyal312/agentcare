from datetime import date

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from app.dependencies import CurrentUser
from app.dependencies import DbSession
from app.schemas.appointment import AppointmentSlotResponse
from app.schemas.appointment import DepartmentResponse
from app.schemas.appointment import DoctorResponse
from app.services.appointment_exceptions import (
    DepartmentNotFoundError,
)
from app.services.appointment_exceptions import (
    InvalidDateRangeError,
)
from app.services.appointment_service import (
    list_departments,
)
from app.services.appointment_service import (
    list_doctors,
)
from app.services.appointment_service import (
    search_available_slots,
)


router = APIRouter(
    prefix="/api/hospital",
    tags=["Hospital"],
)


@router.get(
    "/departments",
    response_model=list[DepartmentResponse],
)
def get_departments(
    current_user: CurrentUser,
    db: DbSession,
):
    return list_departments(db)


@router.get(
    "/departments/{department_id}/doctors",
    response_model=list[DoctorResponse],
)
def get_department_doctors(
    department_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    try:
        return list_doctors(
            db,
            department_id,
        )

    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/availability",
    response_model=list[AppointmentSlotResponse],
)
def get_availability(
    department_id: int,
    start_date: date,
    end_date: date,
    current_user: CurrentUser,
    db: DbSession,
):
    try:
        return search_available_slots(
            db,
            department_id,
            start_date,
            end_date,
        )

    except DepartmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidDateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc