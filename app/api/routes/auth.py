from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import CurrentUser
from app.dependencies import DbSession
from app.schemas.auth import PatientRegisterRequest
from app.schemas.auth import RegistrationResponse
from app.schemas.auth import TokenResponse
from app.schemas.auth import UserResponse
from app.security import create_access_token
from app.services.auth_service import authenticate_user
from app.services.auth_service import create_patient_account
from app.models import User
from app.services.auth_service import AccountAlreadyExistsError


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_patient(
    registration: PatientRegisterRequest,
    db: DbSession,
) -> RegistrationResponse:
    try:
        user, profile = create_patient_account(
            db,
            registration,
        )

    #except ValueError as exc:
    except AccountAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return RegistrationResponse(
        user=UserResponse.model_validate(user),
        patient_profile=profile,
    )


@router.post(
    "/token",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: DbSession,
) -> TokenResponse:
    # OAuth2 calls this field "username".
    # AgentCare uses email addresses as usernames.
    user = authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    token = create_access_token(
        user_id=user.id
    )

    return TokenResponse(
        access_token=token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: CurrentUser,
) -> User:
    return current_user