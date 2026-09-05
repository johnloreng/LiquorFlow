import uuid

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.auth.dependencies import require_role
from app.auth.jwt import create_access_token
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models.customer import Customer
from app.models.enums import UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User


# ============================================================
# TEST ROUTER
# ============================================================

authorization_router = APIRouter(prefix="/test")


@authorization_router.get("/admin-only")
def admin_only(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    return {
        "message": "Admin access granted",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


app.include_router(authorization_router)

client = TestClient(app)


# ============================================================
# HELPERS
# ============================================================

def get_admin():
    db = SessionLocal()
    try:
        admin = (
            db.query(User)
            .filter(User.email == "johnloreng@gmail.com")
            .first()
        )

        assert admin is not None
        assert admin.role == UserRole.ADMIN
        assert admin.is_active is True

        return admin
    finally:
        db.close()


def create_test_user(role: UserRole):
    db = SessionLocal()

    try:
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            name=f"Test {role.value}",
            email=f"test-{role.value.lower()}-{unique_id}@liquorflow.test",
            phone=None,
            password_hash=hash_password("test-password"),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    finally:
        db.close()


def delete_test_user(user_id: int):
    db = SessionLocal()

    try:
        orders = (
            db.query(Order)
            .filter(Order.created_by == user_id)
            .all()
        )

        for order in orders:
            db.query(OrderItem).filter(
                OrderItem.order_id == order.id
            ).delete(
                synchronize_session=False
            )

            db.delete(order)

        db.flush()

        db.query(User).filter(
            User.id == user_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

    finally:
        db.close()


def create_test_product(
    name=None,
    category="Beer",
    price=200.00,
    stock_quantity=10,
    is_active=True,
):
    db = SessionLocal()

    try:
        product = Product(
            name=name or f"Test Product {uuid.uuid4().hex[:8]}",
            category=category,
            price=price,
            stock_quantity=stock_quantity,
            is_active=is_active,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        product_id = product.id

        return product_id

    finally:
        db.close()


def delete_test_product(product_id: int):
    db = SessionLocal()

    try:
        db.query(Product).filter(
            Product.id == product_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

    finally:
        db.close()


def create_test_customer():
    db = SessionLocal()

    try:
        customer = Customer(
            name=f"Test Customer {uuid.uuid4().hex[:8]}",
            phone=f"07{uuid.uuid4().int % 100000000:08d}",
            address="Test Address",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

        return customer_id

    finally:
        db.close()


def delete_test_customer(customer_id: int):
    db = SessionLocal()

    try:
        db.query(Customer).filter(
            Customer.id == customer_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

    finally:
        db.close()


def delete_test_order(order_id: int):
    db = SessionLocal()

    try:
        db.query(OrderItem).filter(
            OrderItem.order_id == order_id
        ).delete(
            synchronize_session=False
        )

        db.query(Order).filter(
            Order.id == order_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

    finally:
        db.close()


def admin_token():
    admin = get_admin()

    return create_access_token(
        user_id=admin.id,
        role=admin.role.value,
    )


def user_token(user):
    return create_access_token(
        user_id=user.id,
        role=user.role.value,
    )


# ============================================================
# ADMIN AUTHORIZATION
# ============================================================

def test_admin_can_access_admin_endpoint():
    admin = get_admin()

    token = admin_token()

    response = client.get(
        "/test/admin-only",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Admin access granted"
    assert data["user_id"] == admin.id
    assert data["role"] == "ADMIN"


# ============================================================
# OTHER ROLES CANNOT ACCESS ADMIN ENDPOINT
# ============================================================

def test_attendant_cannot_access_admin_endpoint():
    user = create_test_user(UserRole.ATTENDANT)

    try:
        response = client.get(
            "/test/admin-only",
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_dispatcher_cannot_access_admin_endpoint():
    user = create_test_user(UserRole.DISPATCHER)

    try:
        response = client.get(
            "/test/admin-only",
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_rider_cannot_access_admin_endpoint():
    user = create_test_user(UserRole.RIDER)

    try:
        response = client.get(
            "/test/admin-only",
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


# ============================================================
# PRODUCT CREATION
# ============================================================

def test_admin_can_create_product():
    token = admin_token()

    response = client.post(
        "/api/products",
        json={
            "name": f"Admin Product {uuid.uuid4().hex[:8]}",
            "category": "Beer",
            "price": 200.00,
            "stock_quantity": 10,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["category"] == "Beer"
    assert data["stock_quantity"] == 10

    product_id = data["id"]

    delete_test_product(product_id)


def test_attendant_cannot_create_product():
    user = create_test_user(UserRole.ATTENDANT)

    try:
        response = client.post(
            "/api/products",
            json={
                "name": "Unauthorized Product",
                "category": "Beer",
                "price": 200.00,
                "stock_quantity": 10,
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_dispatcher_cannot_create_product():
    user = create_test_user(UserRole.DISPATCHER)

    try:
        response = client.post(
            "/api/products",
            json={
                "name": "Unauthorized Product",
                "category": "Beer",
                "price": 200.00,
                "stock_quantity": 10,
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_rider_cannot_create_product():
    user = create_test_user(UserRole.RIDER)

    try:
        response = client.post(
            "/api/products",
            json={
                "name": "Unauthorized Product",
                "category": "Beer",
                "price": 200.00,
                "stock_quantity": 10,
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


# ============================================================
# CUSTOMER CREATION
# ============================================================

def test_admin_can_create_customer():
    response = client.post(
        "/api/customers",
        json={
            "name": "Admin Test Customer",
            "phone": f"070{uuid.uuid4().int % 10000000:07d}",
            "address": "Nakuru",
        },
        headers={
            "Authorization": f"Bearer {admin_token()}"
        },
    )

    assert response.status_code == 201

    customer_id = response.json()["id"]

    delete_test_customer(customer_id)


def test_attendant_can_create_customer():
    user = create_test_user(UserRole.ATTENDANT)

    try:
        response = client.post(
            "/api/customers",
            json={
                "name": "Attendant Test Customer",
                "phone": f"070{uuid.uuid4().int % 10000000:07d}",
                "address": "Nakuru",
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 201

        customer_id = response.json()["id"]

        delete_test_customer(customer_id)

    finally:
        delete_test_user(user.id)


def test_dispatcher_cannot_create_customer():
    user = create_test_user(UserRole.DISPATCHER)

    try:
        response = client.post(
            "/api/customers",
            json={
                "name": "Unauthorized Customer",
                "phone": "0700000003",
                "address": "Nakuru",
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


def test_rider_cannot_create_customer():
    user = create_test_user(UserRole.RIDER)

    try:
        response = client.post(
            "/api/customers",
            json={
                "name": "Unauthorized Customer",
                "phone": "0700000004",
                "address": "Nakuru",
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_user(user.id)


# ============================================================
# ORDER CREATION
# ============================================================

def test_admin_can_create_order():
    customer_id = create_test_customer()
    product_id = create_test_product()

    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        original_stock = product.stock_quantity
        price = product.price

    finally:
        db.close()

    order_id = None

    try:
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
                "Authorization": f"Bearer {admin_token()}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        admin = get_admin()

        assert data["customer_id"] == customer_id
        assert data["created_by"] == admin.id
        assert data["status"] == "PENDING"
        assert data["total_amount"] == str(price)

        order_id = data["id"]

    finally:
        if order_id:
            delete_test_order(order_id)

        db = SessionLocal()

        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            if product:
                product.stock_quantity = original_stock
                db.commit()

        finally:
            db.close()

        delete_test_product(product_id)
        delete_test_customer(customer_id)


def test_attendant_can_create_order():
    user = create_test_user(UserRole.ATTENDANT)
    customer_id = create_test_customer()
    product_id = create_test_product()

    db = SessionLocal()

    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        original_stock = product.stock_quantity
        price = product.price

    finally:
        db.close()

    order_id = None

    try:
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
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["customer_id"] == customer_id
        assert data["created_by"] == user.id
        assert data["status"] == "PENDING"
        assert data["total_amount"] == str(price)

        order_id = data["id"]

    finally:
        if order_id:
            delete_test_order(order_id)

        db = SessionLocal()

        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            if product:
                product.stock_quantity = original_stock
                db.commit()

        finally:
            db.close()

        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


def test_dispatcher_cannot_create_order():
    user = create_test_user(UserRole.DISPATCHER)
    customer_id = create_test_customer()
    product_id = create_test_product()

    try:
        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Unauthorized Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
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
        response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "delivery_address": "Unauthorized Address",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 1,
                    }
                ],
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_customer(customer_id)
        delete_test_user(user.id)


# ============================================================
# PRODUCT UPDATE
# ============================================================

def test_admin_can_update_product():
    product_id = create_test_product()

    try:
        db = SessionLocal()

        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            original_name = product.name

        finally:
            db.close()

        response = client.patch(
            f"/api/products/{product_id}",
            json={
                "name": "Updated Test Product"
            },
            headers={
                "Authorization": f"Bearer {admin_token()}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product_id
        assert data["name"] == "Updated Test Product"

    finally:
        db = SessionLocal()

        try:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            if product:
                product.name = original_name
                db.commit()

        finally:
            db.close()

        delete_test_product(product_id)


def test_attendant_cannot_update_product():
    user = create_test_user(UserRole.ATTENDANT)
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}",
            json={
                "name": "Unauthorized Update"
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_dispatcher_cannot_update_product():
    user = create_test_user(UserRole.DISPATCHER)
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}",
            json={
                "name": "Unauthorized Update"
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_rider_cannot_update_product():
    user = create_test_user(UserRole.RIDER)
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}",
            json={
                "name": "Unauthorized Update"
            },
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_admin_update_product_not_found():
    response = client.patch(
        "/api/products/999999",
        json={
            "name": "Missing Product"
        },
        headers={
            "Authorization": f"Bearer {admin_token()}"
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_admin_can_partially_update_product():
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}",
            json={
                "category": "Updated Category"
            },
            headers={
                "Authorization": f"Bearer {admin_token()}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product_id
        assert data["category"] == "Updated Category"

    finally:
        delete_test_product(product_id)


def test_admin_update_product_rejects_negative_stock():
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}",
            json={
                "stock_quantity": -1
            },
            headers={
                "Authorization": f"Bearer {admin_token()}"
            },
        )

        assert response.status_code == 422

    finally:
        delete_test_product(product_id)


# ============================================================
# PRODUCT DEACTIVATION
# ============================================================

def test_admin_can_deactivate_product():
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}/deactivate",
            headers={
                "Authorization": f"Bearer {admin_token()}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == product_id
        assert data["is_active"] is False

    finally:
        delete_test_product(product_id)


def test_attendant_cannot_deactivate_product():
    user = create_test_user(UserRole.ATTENDANT)
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}/deactivate",
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_dispatcher_cannot_deactivate_product():
    user = create_test_user(UserRole.DISPATCHER)
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}/deactivate",
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_rider_cannot_deactivate_product():
    user = create_test_user(UserRole.RIDER)
    product_id = create_test_product()

    try:
        response = client.patch(
            f"/api/products/{product_id}/deactivate",
            headers={
                "Authorization": f"Bearer {user_token(user)}"
            },
        )

        assert response.status_code == 403

    finally:
        delete_test_product(product_id)
        delete_test_user(user.id)


def test_admin_deactivate_product_not_found():
    response = client.patch(
        "/api/products/999999/deactivate",
        headers={
            "Authorization": f"Bearer {admin_token()}"
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
