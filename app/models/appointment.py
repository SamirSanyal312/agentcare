from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import AppointmentStatus
from app.enums import SlotStatus
from app.models.base import TimestampMixin
from app.models.base import enum_type


class AppointmentSlot(TimestampMixin, Base):
    __tablename__ = "appointment_slots"

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "start_time",
            "end_time",
            name="uq_doctor_slot_time",
        ),
        CheckConstraint(
            "end_time > start_time",
            name="ck_slot_end_after_start",
        ),
        Index(
            "ix_slot_doctor_status_start",
            "doctor_id",
            "status",
            "start_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False,
        index=True,
    )

    start_time: Mapped[datetime] = mapped_column(
        nullable=False,
    )

    end_time: Mapped[datetime] = mapped_column(
        nullable=False,
    )

    status: Mapped[SlotStatus] = mapped_column(
        enum_type(SlotStatus, "slot_status"),
        default=SlotStatus.AVAILABLE,
        server_default=SlotStatus.AVAILABLE.value,
        nullable=False,
        index=True,
    )

    doctor = relationship("Doctor")


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"

    __table_args__ = (
        Index(
            "ix_appointment_patient_status",
            "patient_id",
            "status",
        ),
        Index(
            "ix_appointment_slot_status",
            "slot_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"),
        nullable=False,
        index=True,
    )

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False,
        index=True,
    )

    slot_id: Mapped[int] = mapped_column(
        ForeignKey("appointment_slots.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[AppointmentStatus] = mapped_column(
        enum_type(
            AppointmentStatus,
            "appointment_status",
        ),
        default=AppointmentStatus.PENDING,
        server_default=AppointmentStatus.PENDING.value,
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confirmation_code: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    patient = relationship("PatientProfile")
    doctor = relationship("Doctor")
    slot = relationship("AppointmentSlot")