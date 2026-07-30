from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.config import settings


ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2."""

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plaintext password against its stored hash."""

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT identifying an AgentCare user."""

    if not settings.secret_key:
        raise RuntimeError(
            "SECRET_KEY is not configured. "
            "Set it in the local .env file."
        )

    if len(settings.secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters."
        )

    now = datetime.now(timezone.utc)

    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """
    Validate a JWT and return its user ID.

    Raises InvalidTokenError for invalid/expired tokens.
    """

    if not settings.secret_key:
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM],
        options={
            "require": [
                "sub",
                "exp",
            ]
        },
    )

    if payload.get("type") != "access":
        raise InvalidTokenError(
            "Invalid token type."
        )

    subject = payload.get("sub")

    if subject is None:
        raise InvalidTokenError(
            "Token subject is missing."
        )

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError(
            "Invalid token subject."
        ) from exc