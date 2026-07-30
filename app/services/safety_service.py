from sqlalchemy.orm import Session

from app.agents.exceptions import SafetyAgentError
from app.agents.safety import evaluate_safety
from app.enums import RequestStatus
from app.enums import WorkflowStatus
from app.models import AuditEvent
from app.models import PatientRequest
from app.models import WorkflowRun
from app.schemas.safety import SafetyDecision
from app.services.escalation_service import (
    create_escalation,
)
from app.services.workflow_exceptions import (
    InvalidWorkflowTransitionError,
)

def run_safety_step(
    db: Session,
    workflow: WorkflowRun,
    actor_id: int | None = None,
) -> tuple[
    SafetyDecision,
    WorkflowRun,
    int | None,
]:
    """
    Execute the Safety Agent for a running workflow.

    Safe requests advance to routing_pending.
    Unsafe/uncertain requests pause for human review
    and create a persistent escalation.
    """

    if workflow.status != WorkflowStatus.RUNNING:
        raise InvalidWorkflowTransitionError(
            "Workflow must be running before safety evaluation."
        )

    if workflow.current_step != "coordinator_pending":
        raise InvalidWorkflowTransitionError(
            "Workflow is not ready for the safety step."
        )

    request = db.get(
        PatientRequest,
        workflow.request_id,
    )

    if request is None:
        raise InvalidWorkflowTransitionError(
            "Workflow request no longer exists."
        )

    # ---------------------------------------------------------
    # Run deterministic guardrails + Safety Agent
    # ---------------------------------------------------------

    try:
        decision = evaluate_safety(
            request.request_text
        )

    except SafetyAgentError as exc:
        # There should be no pending business changes here,
        # but rollback first to ensure the session is clean.
        db.rollback()

        workflow = db.get(
            WorkflowRun,
            workflow.id,
        )

        if workflow is None:
            raise

        workflow.status = (
            WorkflowStatus.FAILED_RETRYABLE
        )

        workflow.retry_count += 1
        workflow.last_error = str(exc)

        db.add(
            AuditEvent(
                actor_id=actor_id,
                workflow_run_id=workflow.id,
                action="SAFETY_AGENT_FAILED",
                entity_type="WorkflowRun",
                entity_id=str(workflow.id),
                event_data={
                    "error": str(exc),
                    "retry_count": (
                        workflow.retry_count
                    ),
                },
            )
        )

        db.commit()

        raise

    # ---------------------------------------------------------
    # Merge Safety result into persistent workflow state
    # ---------------------------------------------------------

    state = dict(
        workflow.state_data or {}
    )

    agent_outputs = dict(
        state.get(
            "agent_outputs",
            {},
        )
    )

    agent_outputs["safety"] = (
        decision.model_dump(
            mode="json"
        )
    )

    completed_steps = list(
        state.get(
            "completed_steps",
            [],
        )
    )

    if "safety" not in completed_steps:
        completed_steps.append(
            "safety"
        )

    state["agent_outputs"] = agent_outputs
    state["completed_steps"] = completed_steps

    escalation_id: int | None = None

    # ---------------------------------------------------------
    # SAFE BRANCH
    # ---------------------------------------------------------

    if decision.allow_automation:
        workflow.current_step = (
            "routing_pending"
        )

        workflow.status = (
            WorkflowStatus.RUNNING
        )

        workflow.last_error = None

        request.status = (
            RequestStatus.IN_PROGRESS
        )

        db.add(
            AuditEvent(
                actor_id=actor_id,
                workflow_run_id=workflow.id,
                action="SAFETY_CHECK_PASSED",
                entity_type="WorkflowRun",
                entity_id=str(workflow.id),
                event_data={
                    "classification": (
                        decision.classification
                    ),
                    "confidence": (
                        decision.confidence
                    ),
                    "source": (
                        decision.source
                    ),
                },
            )
        )

    # ---------------------------------------------------------
    # UNSAFE / HUMAN REVIEW BRANCH
    # ---------------------------------------------------------

    else:
        escalation = create_escalation(
            db=db,
            workflow=workflow,
            category=decision.classification,
            reason=decision.reason,
            actor_id=actor_id,
        )

        escalation_id = escalation.id

        state["human_review"] = {
            "required": True,
            "escalation_id": escalation.id,
            "category": decision.classification,
        }

        workflow.current_step = (
            "human_review"
        )

        workflow.status = (
            WorkflowStatus.WAITING_FOR_HUMAN
        )

        workflow.last_error = None

        request.status = (
            RequestStatus.WAITING_FOR_HUMAN
        )

        db.add(
            AuditEvent(
                actor_id=actor_id,
                workflow_run_id=workflow.id,
                action="SAFETY_CHECK_ESCALATED",
                entity_type="WorkflowRun",
                entity_id=str(workflow.id),
                event_data={
                    "classification": (
                        decision.classification
                    ),
                    "confidence": (
                        decision.confidence
                    ),
                    "source": (
                        decision.source
                    ),
                    "escalation_id": (
                        escalation.id
                    ),
                },
            )
        )

    # Important: assign state for BOTH branches.
    workflow.state_data = state

    # ---------------------------------------------------------
    # Persist everything atomically
    # ---------------------------------------------------------

    db.commit()

    db.refresh(workflow)

    return (
        decision,
        workflow,
        escalation_id,
    )