import os

from app import models
from app.auth import hash_password
from app.database import SessionLocal


def create_user(
    username: str,
    full_name: str,
    password: str,
    role: str,
):
    db = SessionLocal()

    try:
        existing = (
            db.query(models.User)
            .filter(models.User.username == username)
            .first()
        )

        if existing:
            print(f"User '{username}' already exists")
            return

        user = models.User(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()

        print(f"Created {role}: {username}")

    finally:
        db.close()


if __name__ == "__main__":
    create_user(
        username=os.getenv("ADMIN_USERNAME", "admin"),
        full_name=os.getenv(
            "ADMIN_FULL_NAME",
            "System Administrator",
        ),
        password=os.environ["ADMIN_PASSWORD"],
        role="ADMIN",
    )

    create_user(
        username=os.getenv(
            "EMPLOYEE_USERNAME",
            "employee",
        ),
        full_name=os.getenv(
            "EMPLOYEE_FULL_NAME",
            "Demo Employee",
        ),
        password=os.environ["EMPLOYEE_PASSWORD"],
        role="EMPLOYEE",
    )