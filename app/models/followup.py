from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import FollowUpStatus
from app.enums import ReminderStatus
from app.models.base import TimestampMixin
from app.models.base import enum_type


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"),
        nullable=False,
        index=True,
    )

    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id"),
        nullable=True,
        index=True,
    )

    reminder_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
    )

    status: Mapped[ReminderStatus] = mapped_column(
        enum_type(
            ReminderStatus,
            "reminder_status",
        ),
        default=ReminderStatus.PENDING,
        server_default=ReminderStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    patient = relationship("PatientProfile")
    appointment = relationship("Appointment")


class FollowUpTask(TimestampMixin, Base):
    __tablename__ = "follow_up_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"),
        nullable=False,
        index=True,
    )

    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id"),
        nullable=True,
        index=True,
    )

    due_at: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[FollowUpStatus] = mapped_column(
        enum_type(
            FollowUpStatus,
            "follow_up_status",
        ),
        default=FollowUpStatus.PENDING,
        server_default=FollowUpStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    patient = relationship("PatientProfile")
    appointment = relationship("Appointment")