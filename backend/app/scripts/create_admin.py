from getpass import getpass

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def main():
    db = SessionLocal()

    try:
        name = input("Admin name: ").strip()
        email = input("Admin email: ").strip().lower()
        phone = input("Admin phone: ").strip() or None
        password = getpass("Admin password: ")

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("A user with this email already exists.")
            return

        admin = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Admin user created successfully: {admin.email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()