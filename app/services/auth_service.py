from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import UserRole
from app.models import AuditEvent
from app.models import PatientProfile
from app.models import User
from app.schemas.auth import PatientRegisterRequest
from app.security import hash_password
from app.security import verify_password

class AccountAlreadyExistsError(Exception):
    """Raised when registration uses an existing email address."""

    pass

def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = normalize_email(email)

    return db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(
        User,
        user_id,
    )


def create_patient_account(
    db: Session,
    registration: PatientRegisterRequest,
) -> tuple[User, PatientProfile]:
    normalized_email = normalize_email(
        str(registration.email)
    )

    existing_user = get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise AccountAlreadyExistsError(
        "An account with this email already exists."
        )

    user = User(
        name=registration.name.strip(),
        email=normalized_email,
        password_hash=hash_password(
            registration.password
        ),
        role=UserRole.PATIENT,
        active=True,
    )

    db.add(user)
    db.flush()

    profile = PatientProfile(
        user_id=user.id,
        date_of_birth=registration.date_of_birth,
        phone=registration.phone,
        preferred_language=(
            registration.preferred_language.strip()
        ),
        emergency_contact=(
            registration.emergency_contact
        ),
    )

    db.add(profile)

    db.add(
        AuditEvent(
            actor_id=user.id,
            action="USER_REGISTERED",
            entity_type="User",
            entity_id=str(user.id),
            event_data={
                "role": UserRole.PATIENT.value,
            },
        )
    )

    db.commit()

    db.refresh(user)
    db.refresh(profile)

    return user, profile


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(
        db,
        email,
    )

    if user is None:
        return None

    if not user.active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user