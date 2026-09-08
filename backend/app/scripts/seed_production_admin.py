import os

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def create_user_if_missing(
    db,
    name,
    email,
    password,
    role,
):
    existing_user = (
        db.query(User)
        .filter(User.email == email.lower())
        .first()
    )

    if existing_user:
        print(
            f"{role.value} already exists: "
            f"{existing_user.email}"
        )
        return

    user = User(
        name=name,
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print(
        f"{role.value} created successfully: "
        f"{user.email}"
    )


def main():
    admin_email = os.getenv("SEED_ADMIN_EMAIL")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD")
    admin_name = os.getenv("SEED_ADMIN_NAME", "John Loreng")

    rider_email = os.getenv("SEED_RIDER_EMAIL")
    rider_password = os.getenv("SEED_RIDER_PASSWORD")
    rider_name = os.getenv("SEED_RIDER_NAME", "LiquorFlow Rider")

    rider2_email = os.getenv("SEED_RIDER2_EMAIL")
    rider2_password = os.getenv("SEED_RIDER2_PASSWORD")
    rider2_name = os.getenv("SEED_RIDER2_NAME", "LiquorFlow Rider 2")

    dispatcher_email = os.getenv("SEED_DISPATCHER_EMAIL")
    dispatcher_password = os.getenv("SEED_DISPATCHER_PASSWORD")
    dispatcher_name = os.getenv(
        "SEED_DISPATCHER_NAME",
        "LiquorFlow Dispatcher",
    )

    if not admin_email or not admin_password:
        print("Production admin seed variables are not configured.")
        return

    if not rider_email or not rider_password:
        print("Production rider seed variables are not configured.")
        return

    if not rider2_email or not rider2_password:
        print("Production second rider seed variables are not configured.")
        return

    if not dispatcher_email or not dispatcher_password:
        print("Production dispatcher seed variables are not configured.")
        return

    db = SessionLocal()

    try:
        create_user_if_missing(
            db=db,
            name=admin_name,
            email=admin_email,
            password=admin_password,
            role=UserRole.ADMIN,
        )

        create_user_if_missing(
            db=db,
            name=rider_name,
            email=rider_email,
            password=rider_password,
            role=UserRole.RIDER,
        )

        create_user_if_missing(
            db=db,
            name=rider2_name,
            email=rider2_email,
            password=rider2_password,
            role=UserRole.RIDER,
        )

        create_user_if_missing(
            db=db,
            name=dispatcher_name,
            email=dispatcher_email,
            password=dispatcher_password,
            role=UserRole.DISPATCHER,
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()