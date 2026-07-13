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
        username="admin",
        full_name="System Administrator",
        password="Admin123!",
        role="ADMIN",
    )

    create_user(
        username="employee",
        full_name="Demo Employee",
        password="Employee123!",
        role="EMPLOYEE",
    )