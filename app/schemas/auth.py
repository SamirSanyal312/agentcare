from datetime import date
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from app.enums import UserRole


class PatientRegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: EmailStr

    password: str = Field(
        min_length=10,
        max_length=128,
    )

    date_of_birth: date | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    preferred_language: str = Field(
        default="English",
        max_length=50,
    )

    emergency_contact: str | None = Field(
        default=None,
        max_length=255,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    email: str
    role: UserRole
    active: bool
    created_at: datetime


class PatientProfileResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int
    date_of_birth: date | None
    phone: str | None
    preferred_language: str
    emergency_contact: str | None


class RegistrationResponse(BaseModel):
    user: UserResponse
    patient_profile: PatientProfileResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"