from __future__ import annotations

from datetime import datetime

#from sqlalchemy import ForeignKey
#from sqlalchemy import Integer
#from sqlalchemy import JSON
#from sqlalchemy import String
#from sqlalchemy import Text

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import ApprovalDecision
from app.enums import EscalationStatus
from app.enums import RequestStatus
from app.enums import WorkflowStatus
from app.models.base import TimestampMixin
from app.models.base import enum_type


class PatientRequest(TimestampMixin, Base):
    __tablename__ = "patient_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"),
        nullable=False,
        index=True,
    )

    request_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[RequestStatus] = mapped_column(
        enum_type(RequestStatus, "request_status"),
        default=RequestStatus.RECEIVED,
        server_default=RequestStatus.RECEIVED.value,
        nullable=False,
        index=True,
    )

    patient = relationship("PatientProfile")


class WorkflowRun(TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"),
        nullable=False,
        index=True,
    )

    request_id: Mapped[int] = mapped_column(
        ForeignKey("patient_requests.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    current_step: Mapped[str] = mapped_column(
        String(100),
        default="created",
        server_default="created",
        nullable=False,
    )

    status: Mapped[WorkflowStatus] = mapped_column(
        enum_type(
            WorkflowStatus,
            "workflow_status",
        ),
        default=WorkflowStatus.CREATED,
        server_default=WorkflowStatus.CREATED.value,
        nullable=False,
        index=True,
    )

    state_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    patient = relationship("PatientProfile")
    request = relationship("PatientRequest")


class Escalation(TimestampMixin, Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(primary_key=True)

    workflow_run_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[EscalationStatus] = mapped_column(
        enum_type(
            EscalationStatus,
            "escalation_status",
        ),
        default=EscalationStatus.OPEN,
        server_default=EscalationStatus.OPEN.value,
        nullable=False,
        index=True,
    )

    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    workflow = relationship("WorkflowRun")
    reviewer = relationship("User")


class Approval(TimestampMixin, Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)

    escalation_id: Mapped[int] = mapped_column(
        ForeignKey("escalations.id"),
        nullable=False,
        index=True,
    )

    reviewed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    decision: Mapped[ApprovalDecision] = mapped_column(
        enum_type(
            ApprovalDecision,
            "approval_decision",
        ),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    escalation = relationship("Escalation")
    reviewer = relationship("User")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    workflow_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_runs.id"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    event_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
    )

    actor = relationship("User")
    workflow = relationship("WorkflowRun")