from datetime import date
from datetime import datetime
from datetime import time
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.enums import AppointmentStatus
from app.enums import SlotStatus
from app.models import Appointment
from app.models import AppointmentSlot
from app.models import AuditEvent
from app.models import Department
from app.models import Doctor
from app.models import PatientProfile
from app.services.appointment_exceptions import (
    AppointmentAccessDeniedError,
)
from app.services.appointment_exceptions import (
    AppointmentNotFoundError,
)
from app.services.appointment_exceptions import (
    DepartmentNotFoundError,
)
from app.services.appointment_exceptions import (
    InvalidAppointmentStateError,
)
from app.services.appointment_exceptions import (
    InvalidDateRangeError,
)
from app.services.appointment_exceptions import (
    SlotNotFoundError,
)
from app.services.appointment_exceptions import (
    SlotUnavailableError,
)


ACTIVE_APPOINTMENT_STATUSES = (
    AppointmentStatus.PENDING,
    AppointmentStatus.CONFIRMED,
)


def generate_confirmation_code() -> str:
    return f"AC-{uuid4().hex[:10].upper()}"


def list_departments(
    db: Session,
) -> list[Department]:
    statement = (
        select(Department)
        .where(
            Department.active.is_(True)
        )
        .order_by(Department.name)
    )

    return list(
        db.scalars(statement).all()
    )


def get_department(
    db: Session,
    department_id: int,
) -> Department:
    department = db.scalar(
        select(Department).where(
            Department.id == department_id,
            Department.active.is_(True),
        )
    )

    if department is None:
        raise DepartmentNotFoundError(
            "Department not found or inactive."
        )

    return department


def list_doctors(
    db: Session,
    department_id: int,
) -> list[Doctor]:
    get_department(
        db,
        department_id,
    )

    statement = (
        select(Doctor)
        .where(
            Doctor.department_id == department_id,
            Doctor.active.is_(True),
        )
        .order_by(Doctor.name)
    )

    return list(
        db.scalars(statement).all()
    )


def search_available_slots(
    db: Session,
    department_id: int,
    start_date: date,
    end_date: date,
) -> list[AppointmentSlot]:
    if end_date < start_date:
        raise InvalidDateRangeError(
            "end_date cannot be before start_date."
        )

    get_department(
        db,
        department_id,
    )

    start_datetime = datetime.combine(
        start_date,
        time.min,
    )

    # Exclusive upper boundary.
    end_datetime = datetime.combine(
        end_date,
        time.max,
    )

    statement = (
        select(AppointmentSlot)
        .join(
            Doctor,
            AppointmentSlot.doctor_id == Doctor.id,
        )
        .where(
            Doctor.department_id == department_id,
            Doctor.active.is_(True),
            AppointmentSlot.status
            == SlotStatus.AVAILABLE,
            AppointmentSlot.start_time
            >= start_datetime,
            AppointmentSlot.start_time
            <= end_datetime,
        )
        .order_by(
            AppointmentSlot.start_time,
            Doctor.name,
        )
    )

    return list(
        db.scalars(statement).all()
    )

def book_appointment(
    db: Session,
    patient: PatientProfile,
    slot_id: int,
    reason: str | None,
    actor_id: int,
) -> Appointment:
    """
    Atomically claim an available slot and create an appointment.
    """

    slot = db.get(
        AppointmentSlot,
        slot_id,
    )

    if slot is None:
        raise SlotNotFoundError(
            "Appointment slot not found."
        )

    doctor = db.get(
        Doctor,
        slot.doctor_id,
    )

    if doctor is None or not doctor.active:
        raise SlotUnavailableError(
            "The doctor for this slot is unavailable."
        )

    # Atomic compare-and-set:
    # update only if the slot is STILL available.
    claim_statement = (
        update(AppointmentSlot)
        .where(
            AppointmentSlot.id == slot_id,
            AppointmentSlot.status
            == SlotStatus.AVAILABLE,
        )
        .values(
            status=SlotStatus.BOOKED,
        )
    )

    result = db.execute(
        claim_statement
    )

    if result.rowcount != 1:
        db.rollback()

        raise SlotUnavailableError(
            "This appointment slot is no longer available."
        )

    # Extra integrity check in case data was manually corrupted.
    existing_appointment = db.scalar(
        select(Appointment).where(
            Appointment.slot_id == slot_id,
            Appointment.status.in_(
                ACTIVE_APPOINTMENT_STATUSES
            ),
        )
    )

    if existing_appointment is not None:
        db.rollback()

        raise SlotUnavailableError(
            "This appointment slot already has an active booking."
        )

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=slot.doctor_id,
        slot_id=slot.id,
        status=AppointmentStatus.CONFIRMED,
        reason=reason.strip() if reason else None,
        confirmation_code=generate_confirmation_code(),
    )

    db.add(appointment)
    db.flush()

    db.add(
        AuditEvent(
            actor_id=actor_id,
            action="APPOINTMENT_BOOKED",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            event_data={
                "patient_id": patient.id,
                "doctor_id": slot.doctor_id,
                "slot_id": slot.id,
                "confirmation_code": (
                    appointment.confirmation_code
                ),
            },
        )
    )

    db.commit()
    db.refresh(appointment)

    return appointment


def list_patient_appointments(
    db: Session,
    patient: PatientProfile,
) -> list[Appointment]:
    statement = (
        select(Appointment)
        .where(
            Appointment.patient_id == patient.id
        )
        .order_by(
            Appointment.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_patient_appointment(
    db: Session,
    patient: PatientProfile,
    appointment_id: int,
) -> Appointment:
    appointment = db.get(
        Appointment,
        appointment_id,
    )

    if appointment is None:
        raise AppointmentNotFoundError(
            "Appointment not found."
        )

    if appointment.patient_id != patient.id:
        raise AppointmentAccessDeniedError(
            "You do not have access to this appointment."
        )

    return appointment


def cancel_appointment(
    db: Session,
    patient: PatientProfile,
    appointment_id: int,
    actor_id: int,
) -> Appointment:
    appointment = get_patient_appointment(
        db,
        patient,
        appointment_id,
    )

    if appointment.status not in ACTIVE_APPOINTMENT_STATUSES:
        raise InvalidAppointmentStateError(
            "Only active appointments can be cancelled."
        )

    slot = db.get(
        AppointmentSlot,
        appointment.slot_id,
    )

    if slot is None:
        raise SlotNotFoundError(
            "Appointment slot not found."
        )

    appointment.status = (
        AppointmentStatus.CANCELLED
    )

    slot.status = SlotStatus.AVAILABLE

    db.add(
        AuditEvent(
            actor_id=actor_id,
            action="APPOINTMENT_CANCELLED",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            event_data={
                "patient_id": patient.id,
                "released_slot_id": slot.id,
            },
        )
    )

    db.commit()
    db.refresh(appointment)

    return appointment


def reschedule_appointment(
    db: Session,
    patient: PatientProfile,
    appointment_id: int,
    new_slot_id: int,
    actor_id: int,
) -> Appointment:
    appointment = get_patient_appointment(
        db,
        patient,
        appointment_id,
    )

    if appointment.status not in ACTIVE_APPOINTMENT_STATUSES:
        raise InvalidAppointmentStateError(
            "Only active appointments can be rescheduled."
        )

    if appointment.slot_id == new_slot_id:
        raise InvalidAppointmentStateError(
            "The new slot must be different "
            "from the current slot."
        )

    new_slot = db.get(
        AppointmentSlot,
        new_slot_id,
    )

    if new_slot is None:
        raise SlotNotFoundError(
            "New appointment slot not found."
        )

    new_doctor = db.get(
        Doctor,
        new_slot.doctor_id,
    )

    if new_doctor is None or not new_doctor.active:
        raise SlotUnavailableError(
            "The doctor for the new slot is unavailable."
        )

    old_slot = db.get(
        AppointmentSlot,
        appointment.slot_id,
    )

    if old_slot is None:
        raise SlotNotFoundError(
            "Existing appointment slot not found."
        )

    claim_statement = (
        update(AppointmentSlot)
        .where(
            AppointmentSlot.id == new_slot_id,
            AppointmentSlot.status
            == SlotStatus.AVAILABLE,
        )
        .values(
            status=SlotStatus.BOOKED,
        )
    )

    result = db.execute(
        claim_statement
    )

    if result.rowcount != 1:
        db.rollback()

        raise SlotUnavailableError(
            "The requested new slot is no longer available."
        )

    old_slot_id = appointment.slot_id
    old_doctor_id = appointment.doctor_id

    appointment.slot_id = new_slot.id
    appointment.doctor_id = new_slot.doctor_id

    old_slot.status = SlotStatus.AVAILABLE

    db.add(
        AuditEvent(
            actor_id=actor_id,
            action="APPOINTMENT_RESCHEDULED",
            entity_type="Appointment",
            entity_id=str(appointment.id),
            event_data={
                "patient_id": patient.id,
                "old_slot_id": old_slot_id,
                "new_slot_id": new_slot.id,
                "old_doctor_id": old_doctor_id,
                "new_doctor_id": new_slot.doctor_id,
            },
        )
    )

    db.commit()
    db.refresh(appointment)

    return appointment



