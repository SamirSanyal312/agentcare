from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.enums import SlotStatus
from app.models import AppointmentSlot
from app.models import Department
from app.models import Doctor
from app.models import DocumentRequirement


DEPARTMENTS = {
    "Cardiology": [
        "Dr. Avery Hart",
        "Dr. Jordan Brooks",
    ],
    "Dermatology": [
        "Dr. Riley Stone",
        "Dr. Cameron Wells",
    ],
    "Orthopedics": [
        "Dr. Morgan Reed",
        "Dr. Taylor Grant",
    ],
    "Neurology": [
        "Dr. Casey Lane",
        "Dr. Parker Evans",
    ],
    "General Medicine": [
        "Dr. Jamie Cole",
        "Dr. Robin Hayes",
    ],
    "ENT": [
        "Dr. Alex Monroe",
        "Dr. Quinn Bailey",
    ],
}


DOCUMENT_REQUIREMENTS = {
    "Cardiology": [
        (
            "ecg",
            "Previous ECG, when available for a follow-up request.",
        ),
        (
            "referral",
            "Referral document when required by hospital policy.",
        ),
    ],
    "Orthopedics": [
        (
            "prior_imaging_report",
            "Previous imaging report when available.",
        ),
    ],
    "Neurology": [
        (
            "referral",
            "Referral document when required by hospital policy.",
        ),
    ],
}


def get_or_create_department(session, name: str) -> Department:
    department = session.scalar(
        select(Department).where(
            Department.name == name
        )
    )

    if department:
        return department

    department = Department(
        name=name,
        description=(
            f"Synthetic {name} department used "
            "for AgentCare demonstration."
        ),
    )

    session.add(department)
    session.flush()

    return department


def get_or_create_doctor(
    session,
    department: Department,
    doctor_name: str,
) -> Doctor:
    doctor = session.scalar(
        select(Doctor).where(
            Doctor.department_id == department.id,
            Doctor.name == doctor_name,
        )
    )

    if doctor:
        return doctor

    doctor = Doctor(
        department_id=department.id,
        name=doctor_name,
    )

    session.add(doctor)
    session.flush()

    return doctor


def seed_document_requirements(
    session,
    department: Department,
) -> None:
    requirements = DOCUMENT_REQUIREMENTS.get(
        department.name,
        [],
    )

    for document_type, description in requirements:
        existing = session.scalar(
            select(DocumentRequirement).where(
                DocumentRequirement.department_id
                == department.id,
                DocumentRequirement.document_type
                == document_type,
            )
        )

        if existing:
            continue

        session.add(
            DocumentRequirement(
                department_id=department.id,
                document_type=document_type,
                description=description,
            )
        )


def seed_slots(
    session,
    doctor: Doctor,
    days: int = 14,
) -> None:
    now = datetime.now(timezone.utc)

    slot_times = [
        (9, 0),
        (10, 30),
        (13, 30),
        (15, 0),
    ]

    for offset in range(1, days + 1):
        slot_date = (now + timedelta(days=offset)).date()

        # Monday-Friday only.
        if slot_date.weekday() >= 5:
            continue

        for hour, minute in slot_times:
            start_time = datetime.combine(
                slot_date,
                time(
                    hour=hour,
                    minute=minute,
                    tzinfo=timezone.utc,
                ),
            )

            end_time = start_time + timedelta(
                minutes=30
            )

            existing = session.scalar(
                select(AppointmentSlot).where(
                    AppointmentSlot.doctor_id
                    == doctor.id,
                    AppointmentSlot.start_time
                    == start_time,
                    AppointmentSlot.end_time
                    == end_time,
                )
            )

            if existing:
                continue

            session.add(
                AppointmentSlot(
                    doctor_id=doctor.id,
                    start_time=start_time,
                    end_time=end_time,
                    status=SlotStatus.AVAILABLE,
                )
            )


def main() -> None:
    session = SessionLocal()

    try:
        for department_name, doctors in DEPARTMENTS.items():
            department = get_or_create_department(
                session,
                department_name,
            )

            seed_document_requirements(
                session,
                department,
            )

            for doctor_name in doctors:
                doctor = get_or_create_doctor(
                    session,
                    department,
                    doctor_name,
                )

                seed_slots(
                    session,
                    doctor,
                )

        session.commit()

        print(
            "AgentCare synthetic hospital data seeded successfully."
        )

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()