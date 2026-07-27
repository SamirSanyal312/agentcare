from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import DocumentStatus
from app.models.base import TimestampMixin
from app.models.base import enum_type


class PatientDocument(TimestampMixin, Base):
    __tablename__ = "patient_documents"

    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "checksum",
            name="uq_patient_document_checksum",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"),
        nullable=False,
        index=True,
    )

    workflow_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=True,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        index=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    storage_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    document_date: Mapped[date | None] = mapped_column(
        nullable=True,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        enum_type(
            DocumentStatus,
            "document_status",
        ),
        default=DocumentStatus.UPLOADED,
        server_default=DocumentStatus.UPLOADED.value,
        nullable=False,
    )

    patient = relationship("PatientProfile")
    workflow = relationship("WorkflowRun")


class DocumentRequirement(TimestampMixin, Base):
    __tablename__ = "document_requirements"

    __table_args__ = (
        UniqueConstraint(
            "department_id",
            "document_type",
            name="uq_department_document_requirement",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    department = relationship("Department")