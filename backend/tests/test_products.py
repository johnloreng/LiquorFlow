from decimal import Decimal

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models.enums import UserRole
from app.models.product import Product
from app.models.user import User


client = TestClient(app)


def create_test_user(role: UserRole):
    db = SessionLocal()

    user = User(
        name=f"Product Test {role.value}",
        email=f"product_test_{role.value.lower()}@example.com",
        phone=None,
        password_hash="test-password-hash",
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id
    db.close()

    return user


def delete_test_user(user_id: int):
    db = SessionLocal()

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user:
        db.delete(user)
        db.commit()

    db.close()


def get_test_product():
    db = SessionLocal()

    product = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .first()
    )

    db.close()

    return product


def get_token(user):
    return create_access_token(
        user_id=user.id,
        role=user.role.value,
    )


def test_admin_can_update_product():
    user = create_test_user(UserRole.ADMIN)

    db = SessionLocal()
    product = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .first()
    )

    assert product is not None

    original_name = product.name

    db.close()

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}",
            json={
                "name": "Updated Test Product",
                "price": "150.00",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product.id
        assert data["name"] == "Updated Test Product"
        assert data["price"] == "150.00"

    finally:
        db = SessionLocal()

        product = (
            db.query(Product)
            .filter(Product.id == product.id)
            .first()
        )

        if product:
            product.name = original_name
            product.price = Decimal("100.00")
            db.commit()

        db.close()

        delete_test_user(user.id)


def test_attendant_cannot_update_product():
    user = create_test_user(UserRole.ATTENDANT)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}",
            json={
                "name": "Unauthorized Update",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_dispatcher_cannot_update_product():
    user = create_test_user(UserRole.DISPATCHER)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}",
            json={
                "name": "Unauthorized Update",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_rider_cannot_update_product():
    user = create_test_user(UserRole.RIDER)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}",
            json={
                "name": "Unauthorized Update",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_admin_can_deactivate_product():
    user = create_test_user(UserRole.ADMIN)
    product = get_test_product()

    assert product is not None

    original_status = product.is_active

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}/status",
            json={
                "is_active": False,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product.id
        assert data["is_active"] is False

    finally:
        db = SessionLocal()

        product = (
            db.query(Product)
            .filter(Product.id == product.id)
            .first()
        )

        if product:
            product.is_active = original_status
            db.commit()

        db.close()

        delete_test_user(user.id)


def test_admin_can_reactivate_product():
    user = create_test_user(UserRole.ADMIN)
    product = get_test_product()

    assert product is not None

    original_status = product.is_active

    try:
        db = SessionLocal()

        product_db = (
            db.query(Product)
            .filter(Product.id == product.id)
            .first()
        )

        product_db.is_active = False
        db.commit()
        db.close()

        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}/status",
            json={
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product.id
        assert data["is_active"] is True

    finally:
        db = SessionLocal()

        product = (
            db.query(Product)
            .filter(Product.id == product.id)
            .first()
        )

        if product:
            product.is_active = original_status
            db.commit()

        db.close()

        delete_test_user(user.id)


def test_attendant_cannot_change_product_status():
    user = create_test_user(UserRole.ATTENDANT)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}/status",
            json={
                "is_active": False,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_dispatcher_cannot_change_product_status():
    user = create_test_user(UserRole.DISPATCHER)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}/status",
            json={
                "is_active": False,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_rider_cannot_change_product_status():
    user = create_test_user(UserRole.RIDER)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}/status",
            json={
                "is_active": False,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_update_nonexistent_product_returns_404():
    user = create_test_user(UserRole.ADMIN)

    try:
        token = get_token(user)

        response = client.patch(
            "/api/products/999999",
            json={
                "name": "Missing Product",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"

    finally:
        delete_test_user(user.id)


def test_change_status_nonexistent_product_returns_404():
    user = create_test_user(UserRole.ADMIN)

    try:
        token = get_token(user)

        response = client.patch(
            "/api/products/999999/status",
            json={
                "is_active": False,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"

    finally:
        delete_test_user(user.id)


def test_invalid_product_update_returns_422():
    user = create_test_user(UserRole.ADMIN)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}",
            json={
                "price": -10,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_user(user.id)


def test_product_status_requires_boolean():
    user = create_test_user(UserRole.ADMIN)
    product = get_test_product()

    assert product is not None

    try:
        token = get_token(user)

        response = client.patch(
            f"/api/products/{product.id}/status",
            json={
                "is_active": "not-a-boolean",
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_user(user.id)