from getpass import getpass

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def prompt_role() -> UserRole:
    roles = list(UserRole)

    print("Select a role:")
    for i, role in enumerate(roles, start=1):
        print(f"  {i}. {role.value}")

    while True:
        choice = input(f"Enter 1-{len(roles)}: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(roles):
            return roles[int(choice) - 1]

        print("Invalid choice, try again.")


def main():
    db = SessionLocal()

    try:
        name = input("Name: ").strip()
        email = input("Email: ").strip().lower()
        phone = input("Phone (optional): ").strip() or None
        role = prompt_role()
        password = getpass("Password: ")

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("A user with this email already exists.")
            return

        user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(
            f"{role.value} user created successfully: "
            f"id={user.id} email={user.email}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()