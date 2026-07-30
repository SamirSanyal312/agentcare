from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import RequestStatus
from app.enums import WorkflowStatus
from app.models import AuditEvent
from app.models import PatientProfile
from app.models import PatientRequest
from app.models import WorkflowRun
from app.services.workflow_exceptions import (
    InvalidWorkflowTransitionError,
)
from app.services.workflow_exceptions import (
    PatientRequestAccessDeniedError,
)
from app.services.workflow_exceptions import (
    PatientRequestNotFoundError,
)
from app.services.workflow_exceptions import (
    WorkflowNotFoundError,
)

def create_patient_request(
    db: Session,
    patient: PatientProfile,
    request_text: str,
    actor_id: int,
) -> tuple[PatientRequest, WorkflowRun]:
    """
    Create the administrative request and its persistent workflow.

    Both are created in one SQL transaction.
    """

    cleaned_text = request_text.strip()

    request = PatientRequest(
        patient_id=patient.id,
        request_text=cleaned_text,
        status=RequestStatus.RECEIVED,
    )

    db.add(request)
    db.flush()

    workflow = WorkflowRun(
        patient_id=patient.id,
        request_id=request.id,
        current_step="request_received",
        status=WorkflowStatus.CREATED,
        state_data={
            "request": {
                "id": request.id,
                "text": cleaned_text,
            },
            "completed_steps": [],
            "agent_outputs": {},
            "tool_results": {},
        },
        retry_count=0,
    )

    db.add(workflow)
    db.flush()

    db.add(
        AuditEvent(
            actor_id=actor_id,
            workflow_run_id=workflow.id,
            action="PATIENT_REQUEST_CREATED",
            entity_type="PatientRequest",
            entity_id=str(request.id),
            event_data={
                "patient_id": patient.id,
                "workflow_run_id": workflow.id,
            },
        )
    )

    db.commit()

    db.refresh(request)
    db.refresh(workflow)

    return request, workflow

def get_patient_request(
    db: Session,
    patient: PatientProfile,
    request_id: int,
) -> PatientRequest:
    request = db.get(
        PatientRequest,
        request_id,
    )

    if request is None:
        raise PatientRequestNotFoundError(
            "Patient request not found."
        )

    if request.patient_id != patient.id:
        raise PatientRequestAccessDeniedError(
            "You do not have access to this request."
        )

    return request

def list_patient_requests(
    db: Session,
    patient: PatientProfile,
) -> list[PatientRequest]:
    statement = (
        select(PatientRequest)
        .where(
            PatientRequest.patient_id == patient.id
        )
        .order_by(
            PatientRequest.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def list_patient_requests(
    db: Session,
    patient: PatientProfile,
) -> list[PatientRequest]:
    statement = (
        select(PatientRequest)
        .where(
            PatientRequest.patient_id == patient.id
        )
        .order_by(
            PatientRequest.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_request_workflow(
    db: Session,
    patient: PatientProfile,
    request_id: int,
) -> WorkflowRun:
    request = get_patient_request(
        db,
        patient,
        request_id,
    )

    workflow = db.scalar(
        select(WorkflowRun).where(
            WorkflowRun.request_id == request.id
        )
    )

    if workflow is None:
        raise WorkflowNotFoundError(
            "Workflow not found for this request."
        )

    return workflow


def update_workflow_state(
    db: Session,
    workflow: WorkflowRun,
    *,
    current_step: str,
    workflow_status: WorkflowStatus,
    request_status: RequestStatus | None = None,
    state_patch: dict | None = None,
    actor_id: int | None = None,
    audit_action: str = "WORKFLOW_STATE_UPDATED",
) -> WorkflowRun:
    """
    Persist a workflow transition.

    state_patch is merged into the existing state_data.
    """

    current_state = dict(
        workflow.state_data or {}
    )

    if state_patch:
        current_state.update(
            state_patch
        )

    previous_step = workflow.current_step
    previous_status = workflow.status

    workflow.current_step = current_step
    workflow.status = workflow_status

    # Assign a new dict instead of mutating the existing JSON object.
    # This ensures SQLAlchemy detects the change reliably.
    workflow.state_data = current_state

    if request_status is not None:
        request = db.get(
            PatientRequest,
            workflow.request_id,
        )

        if request is None:
            raise PatientRequestNotFoundError(
                "Workflow request no longer exists."
            )

        request.status = request_status

    db.add(
        AuditEvent(
            actor_id=actor_id,
            workflow_run_id=workflow.id,
            action=audit_action,
            entity_type="WorkflowRun",
            entity_id=str(workflow.id),
            event_data={
                "previous_step": previous_step,
                "current_step": current_step,
                "previous_status": previous_status.value,
                "current_status": workflow_status.value,
            },
        )
    )

    db.commit()
    db.refresh(workflow)

    return workflow


def start_workflow(
    db: Session,
    workflow: WorkflowRun,
    actor_id: int | None = None,
) -> WorkflowRun:
    if workflow.status != WorkflowStatus.CREATED:
        raise InvalidWorkflowTransitionError(
            "Only newly created workflows can be started."
        )

    return update_workflow_state(
        db=db,
        workflow=workflow,
        current_step="coordinator_pending",
        workflow_status=WorkflowStatus.RUNNING,
        request_status=RequestStatus.IN_PROGRESS,
        state_patch={
            "workflow_started": True,
        },
        actor_id=actor_id,
        audit_action="WORKFLOW_STARTED",
    )


def pause_for_human_review(
    db: Session,
    workflow: WorkflowRun,
    reason: str,
    actor_id: int | None = None,
) -> WorkflowRun:
    return update_workflow_state(
        db=db,
        workflow=workflow,
        current_step="human_review",
        workflow_status=WorkflowStatus.WAITING_FOR_HUMAN,
        request_status=RequestStatus.WAITING_FOR_HUMAN,
        state_patch={
            "human_review": {
                "required": True,
                "reason": reason,
            }
        },
        actor_id=actor_id,
        audit_action="WORKFLOW_PAUSED_FOR_HUMAN",
    )


def complete_workflow(
    db: Session,
    workflow: WorkflowRun,
    actor_id: int | None = None,
) -> WorkflowRun:
    if workflow.status not in {
        WorkflowStatus.RUNNING,
        WorkflowStatus.WAITING_FOR_HUMAN,
    }:
        raise InvalidWorkflowTransitionError(
            "This workflow cannot be completed "
            "from its current state."
        )

    return update_workflow_state(
        db=db,
        workflow=workflow,
        current_step="completed",
        workflow_status=WorkflowStatus.COMPLETED,
        request_status=RequestStatus.COMPLETED,
        state_patch={
            "workflow_completed": True,
        },
        actor_id=actor_id,
        audit_action="WORKFLOW_COMPLETED",
    )


def mark_workflow_retryable_failure(
    db: Session,
    workflow: WorkflowRun,
    error_message: str,
    actor_id: int | None = None,
) -> WorkflowRun:
    workflow.retry_count += 1
    workflow.last_error = error_message

    return update_workflow_state(
        db=db,
        workflow=workflow,
        current_step=workflow.current_step,
        workflow_status=WorkflowStatus.FAILED_RETRYABLE,
        request_status=RequestStatus.IN_PROGRESS,
        state_patch={
            "last_failure": {
                "message": error_message,
                "retry_count": workflow.retry_count,
            }
        },
        actor_id=actor_id,
        audit_action="WORKFLOW_RETRYABLE_FAILURE",
    )


def resume_retryable_workflow(
    db: Session,
    workflow: WorkflowRun,
    actor_id: int | None = None,
) -> WorkflowRun:
    if workflow.status != WorkflowStatus.FAILED_RETRYABLE:
        raise InvalidWorkflowTransitionError(
            "Only retryable failed workflows can be resumed."
        )

    workflow.last_error = None

    return update_workflow_state(
        db=db,
        workflow=workflow,
        current_step=workflow.current_step,
        workflow_status=WorkflowStatus.RUNNING,
        request_status=RequestStatus.IN_PROGRESS,
        actor_id=actor_id,
        audit_action="WORKFLOW_RESUMED",
    )


