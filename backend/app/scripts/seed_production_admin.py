import os

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def main():
    email = os.getenv("SEED_ADMIN_EMAIL")
    password = os.getenv("SEED_ADMIN_PASSWORD")
    name = os.getenv("SEED_ADMIN_NAME", "John Loreng")

    if not email or not password:
        print("Production admin seed variables are not configured.")
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.email == email.lower())
            .first()
        )

        if existing_user:
            print(f"Production admin already exists: {existing_user.email}")
            return

        admin = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Production admin created: {admin.email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
