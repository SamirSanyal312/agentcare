from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select

from app.dependencies import DbSession
from app.dependencies import require_roles
from app.enums import UserRole
from app.models import User
from app.schemas.auth import UserResponse


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
)


AdminUser = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.ADMIN,
        )
    ),
]


@router.get(
    "/users",
    response_model=list[UserResponse],
)
def list_users(
    current_user: AdminUser,
    db: DbSession,
) -> list[User]:
    statement = (
        select(User)
        .order_by(User.id)
    )

    return list(
        db.scalars(statement).all()
    )