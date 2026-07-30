from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.enums import RequestStatus
from app.enums import WorkflowStatus


class PatientRequestCreate(BaseModel):
    request_text: str = Field(
        min_length=5,
        max_length=2000,
    )


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    patient_id: int
    request_id: int
    current_step: str
    status: WorkflowStatus
    state_data: dict
    retry_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class PatientRequestResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    patient_id: int
    request_text: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime


class RequestWithWorkflowResponse(BaseModel):
    request: PatientRequestResponse
    workflow: WorkflowRunResponse