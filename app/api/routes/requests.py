from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.dependencies import CurrentUser
from app.dependencies import DbSession
from app.dependencies import get_current_patient_profile
from app.models import PatientProfile
from app.schemas.workflow import PatientRequestCreate
from app.schemas.workflow import PatientRequestResponse
from app.schemas.workflow import RequestWithWorkflowResponse
from app.schemas.workflow import WorkflowRunResponse
from app.services.workflow_exceptions import (
    PatientRequestAccessDeniedError,
)
from app.services.workflow_exceptions import (
    PatientRequestNotFoundError,
)
from app.services.workflow_exceptions import (
    WorkflowNotFoundError,
)
from app.services.workflow_service import (
    create_patient_request,
)
from app.services.workflow_service import (
    get_patient_request,
)
from app.services.workflow_service import (
    get_request_workflow,
)
from app.services.workflow_service import (
    list_patient_requests,
)


router = APIRouter(
    prefix="/api/requests",
    tags=["Patient Requests"],
)


@router.post(
    "",
    response_model=RequestWithWorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_request(
    request_data: PatientRequestCreate,
    current_user: CurrentUser,
    db: DbSession,
    patient: PatientProfile = Depends(
        get_current_patient_profile
    ),
) -> RequestWithWorkflowResponse:
    request, workflow = create_patient_request(
        db=db,
        patient=patient,
        request_text=request_data.request_text,
        actor_id=current_user.id,
    )

    return RequestWithWorkflowResponse(
        request=request,
        workflow=workflow,
    )


@router.get(
    "",
    response_model=list[PatientRequestResponse],
)
def get_my_requests(
    db: DbSession,
    patient: PatientProfile = Depends(
        get_current_patient_profile
    ),
):
    return list_patient_requests(
        db,
        patient,
    )


@router.get(
    "/{request_id}",
    response_model=PatientRequestResponse,
)
def get_my_request(
    request_id: int,
    db: DbSession,
    patient: PatientProfile = Depends(
        get_current_patient_profile
    ),
):
    try:
        return get_patient_request(
            db,
            patient,
            request_id,
        )

    except PatientRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PatientRequestAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/{request_id}/workflow",
    response_model=WorkflowRunResponse,
)
def get_my_request_workflow(
    request_id: int,
    db: DbSession,
    patient: PatientProfile = Depends(
        get_current_patient_profile
    ),
):
    try:
        return get_request_workflow(
            db,
            patient,
            request_id,
        )

    except PatientRequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PatientRequestAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except WorkflowNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


