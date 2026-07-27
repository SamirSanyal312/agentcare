from datetime import datetime
from enum import Enum as PythonEnum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class TimestampMixin:
    """Reusable created/updated timestamp fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def enum_type(enum_class: type[PythonEnum], name: str) -> SQLEnum:
    """
    Store enum values as strings.

    native_enum=False keeps the schema portable between SQLite
    development and PostgreSQL deployment.
    """

    return SQLEnum(
        enum_class,
        values_callable=lambda enum_members: [
            member.value for member in enum_members
        ],
        name=name,
        native_enum=False,
        validate_strings=True,
    )