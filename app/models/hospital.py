from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    doctors: Mapped[list["Doctor"]] = relationship(
        "Doctor",
        back_populates="department",
    )


class Doctor(TimestampMixin, Base):
    __tablename__ = "doctors"

    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "name",
            name="uq_doctor_department_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="doctors",
    )