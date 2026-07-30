from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.enums import AppointmentStatus
from app.enums import SlotStatus


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    description: str | None
    active: bool


class DoctorResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    department_id: int
    name: str
    active: bool


class AppointmentSlotResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    doctor_id: int
    start_time: datetime
    end_time: datetime
    status: SlotStatus


class AppointmentCreateRequest(BaseModel):
    slot_id: int

    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    patient_id: int
    doctor_id: int
    slot_id: int
    status: AppointmentStatus
    reason: str | None
    confirmation_code: str | None
    created_at: datetime
    updated_at: datetime


class RescheduleAppointmentRequest(BaseModel):
    new_slot_id: int


class AvailabilityQuery(BaseModel):
    department_id: int
    start_date: date
    end_date: date