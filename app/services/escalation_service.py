from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import EscalationStatus
from app.models import AuditEvent
from app.models import Escalation
from app.models import WorkflowRun


def create_escalation(
    db: Session,
    workflow: WorkflowRun,
    category: str,
    reason: str,
    actor_id: int | None = None,
) -> Escalation:
    """
    Create or return an existing open escalation
    for this workflow/category.
    """

    existing = db.scalar(
        select(Escalation).where(
            Escalation.workflow_run_id
            == workflow.id,
            Escalation.category
            == category,
            Escalation.status.in_(
                [
                    EscalationStatus.OPEN,
                    EscalationStatus.IN_REVIEW,
                ]
            ),
        )
    )

    if existing is not None:
        return existing

    escalation = Escalation(
        workflow_run_id=workflow.id,
        category=category,
        reason=reason,
        status=EscalationStatus.OPEN,
    )

    db.add(escalation)
    db.flush()

    db.add(
        AuditEvent(
            actor_id=actor_id,
            workflow_run_id=workflow.id,
            action="ESCALATION_CREATED",
            entity_type="Escalation",
            entity_id=str(escalation.id),
            event_data={
                "category": category,
                "reason": reason,
            },
        )
    )

    return escalation