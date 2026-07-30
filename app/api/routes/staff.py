from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import DbSession
from app.dependencies import require_roles
from app.enums import UserRole
from app.models import Escalation
from app.models import User
from app.schemas.staff import EscalationSummary


router = APIRouter(
    prefix="/api/staff",
    tags=["Staff"],
)


StaffUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.STAFF,
            UserRole.ADMIN,
        )
    ),
]


@router.get(
    "/escalations",
    response_model=list[EscalationSummary],
)
def get_escalations(
    current_user: StaffUser,
    db: DbSession,
) -> list[Escalation]:
    statement = (
        select(Escalation)
        .order_by(
            Escalation.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )