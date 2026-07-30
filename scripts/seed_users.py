from sqlalchemy import select

from app.database import SessionLocal
from app.enums import UserRole
from app.models import User
from app.security import hash_password


DEMO_USERS = [
    {
        "name": "AgentCare Staff",
        "email": "staff@agentcare.demo",
        "password": "DemoStaff123!",
        "role": UserRole.STAFF,
    },
    {
        "name": "AgentCare Administrator",
        "email": "admin@agentcare.demo",
        "password": "DemoAdmin123!",
        "role": UserRole.ADMIN,
    },
]


def main() -> None:
    db = SessionLocal()

    try:
        for demo_user in DEMO_USERS:
            existing = db.scalar(
                select(User).where(
                    User.email == demo_user["email"]
                )
            )

            if existing is not None:
                print(
                    f"Skipping existing user: "
                    f"{demo_user['email']}"
                )
                continue

            user = User(
                name=demo_user["name"],
                email=demo_user["email"],
                password_hash=hash_password(
                    demo_user["password"]
                ),
                role=demo_user["role"],
                active=True,
            )

            db.add(user)

        db.commit()

        print(
            "Synthetic AgentCare staff accounts seeded."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()