from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import UserRole
from app.models.base import TimestampMixin
from app.models.base import enum_type


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        enum_type(UserRole, "user_role"),
        default=UserRole.PATIENT,
        server_default=UserRole.PATIENT.value,
        index=True,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    patient_profile: Mapped["PatientProfile | None"] = relationship(
        "PatientProfile",
        back_populates="user",
        uselist=False,
    )


class PatientProfile(TimestampMixin, Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    preferred_language: Mapped[str] = mapped_column(
        String(50),
        default="English",
        server_default="English",
        nullable=False,
    )

    emergency_contact: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="patient_profile",
    )