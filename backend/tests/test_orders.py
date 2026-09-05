from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.enums import UserRole
from tests.test_authorization import (
    create_test_customer,
    create_test_product,
    create_test_user,
    delete_test_customer,
    delete_test_order,
    delete_test_product,
    delete_test_user,
    user_token,
)


client = TestClient(app)


# ============================================================
# CREATE ORDER
# ============================================================

def test_admin_can_create_order():
    user = create_test_user(UserRole.ADMIN)
    customer_id = create_test_customer()
    product_id = create_test_product(
        price=200.00,
        stock_quantity=10,
    )

    order_id = None

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Delivery Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 2,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["customer_id"] == customer_id
        assert data["created_by"] == user.id
        assert data["delivery_address"] == "Test Delivery Address"
        assert data["status"] == "PENDING"
        assert data["total_amount"] == "400.00"

        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == product_id
        assert data["items"][0]["quantity"] == 2
        assert data["items"][0]["unit_price"] == "200.00"
        assert data["items"][0]["subtotal"] == "400.00"

        order_id = data["id"]

        db = SessionLocal()

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        assert product is not None
        assert product.stock_quantity == 8

        db.close()

    finally:
        if order_id is not None:
            delete_test_order(order_id)

        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


def test_attendant_can_create_order():
    user = create_test_user(UserRole.ATTENDANT)
    customer_id = create_test_customer()
    product_id = create_test_product(
        price=150.00,
        stock_quantity=5,
    )

    order_id = None

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Attendant Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["created_by"] == user.id
        assert data["total_amount"] == "150.00"

        order_id = data["id"]

    finally:
        if order_id is not None:
            delete_test_order(order_id)

        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


# ============================================================
# AUTHORIZATION
# ============================================================

def test_dispatcher_cannot_create_order():
    user = create_test_user(UserRole.DISPATCHER)
    customer_id = create_test_customer()
    product_id = create_test_product()

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


def test_rider_cannot_create_order():
    user = create_test_user(UserRole.RIDER)
    customer_id = create_test_customer()
    product_id = create_test_product()

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)

# ============================================================
# ORDER VALIDATION
# ============================================================

def test_order_rejects_nonexistent_customer():
    user = create_test_user(UserRole.ADMIN)
    product_id = create_test_product()

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": 999999999,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Customer not found"

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_order_rejects_nonexistent_product():
    user = create_test_user(UserRole.ADMIN)
    customer_id = create_test_customer()

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": 999999999,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404

        assert (
            "not found or inactive"
            in response.json()["detail"]
        )

    finally:
        delete_test_customer(customer_id)
        delete_test_user(user.id)


def test_order_rejects_inactive_product():
    user = create_test_user(UserRole.ADMIN)
    customer_id = create_test_customer()

    product_id = create_test_product(
        price=200.00,
        stock_quantity=10,
        is_active=False,
    )

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 404

        assert (
            "not found or inactive"
            in response.json()["detail"]
        )

    finally:
        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


def test_order_rejects_insufficient_stock():
    user = create_test_user(UserRole.ADMIN)
    customer_id = create_test_customer()

    product_id = create_test_product(
        price=200.00,
        stock_quantity=2,
    )

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 5,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 400

        assert (
            "Insufficient stock"
            in response.json()["detail"]
        )

        # Make sure failed order did not reduce stock.
        db = SessionLocal()

        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        assert product is not None
        assert product.stock_quantity == 2

        db.close()

    finally:
        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


# ============================================================
# ORDER INPUT VALIDATION
# ============================================================

def test_order_rejects_empty_items():
    user = create_test_user(UserRole.ADMIN)
    customer_id = create_test_customer()

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_customer(customer_id)
        delete_test_user(user.id)


def test_order_rejects_zero_quantity():
    user = create_test_user(UserRole.ADMIN)
    customer_id = create_test_customer()
    product_id = create_test_product()

    try:
        token = user_token(user)

        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Test Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 0,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)