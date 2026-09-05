from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models.customer import Customer
from app.models.enums import UserRole
from app.models.user import User
from tests.test_authorization import create_test_user, delete_test_user


client = TestClient(app)


def test_admin_can_create_customer():
    user = create_test_user(UserRole.ADMIN)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "Test Customer",
                "phone": "0700342319",
                "address": "Test Address",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == "Test Customer"
        assert data["phone"] == "0700342319"
        assert data["address"] == "Test Address"

        db = SessionLocal()
        customer = (
            db.query(Customer)
            .filter(Customer.id == data["id"])
            .first()
        )

        if customer:
            db.delete(customer)
            db.commit()

        db.close()

    finally:
        delete_test_user(user.id)


def test_attendant_can_create_customer():
    user = create_test_user(UserRole.ATTENDANT)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "Attendant Customer",
                "phone": "0700345678",
                "address": "Attendant Address",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        db = SessionLocal()
        customer = (
            db.query(Customer)
            .filter(Customer.id == data["id"])
            .first()
        )

        if customer:
            db.delete(customer)
            db.commit()

        db.close()

    finally:
        delete_test_user(user.id)


def test_dispatcher_cannot_create_customer():
    user = create_test_user(UserRole.DISPATCHER)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "Unauthorized Customer",
                "phone": "0763345678",
                "address": "Test Address",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_rider_cannot_create_customer():
    user = create_test_user(UserRole.RIDER)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "Unauthorized Customer",
                "phone": "0740345678",
                "address": "Test Address",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_customer_validation_rejects_empty_name():
    user = create_test_user(UserRole.ADMIN)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "",
                "phone": "0750345678",
                "address": "Test Address",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_user(user.id)


def test_customer_validation_rejects_empty_phone():
    user = create_test_user(UserRole.ADMIN)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "Test Customer",
                "phone": "",
                "address": "Test Address",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_user(user.id)


def test_customer_validation_rejects_empty_address():
    user = create_test_user(UserRole.ADMIN)

    try:
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
        )

        response = client.post(
            "/api/customers",
            json={
                "name": "Test Customer",
                "phone": "0786345678",
                "address": "",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_user(user.id)
