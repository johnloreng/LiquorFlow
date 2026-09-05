from decimal import Decimal
import uuid

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.customer import Customer
from app.models.delivery import Delivery
from app.models.delivery_status_history import DeliveryStatusHistory
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.auth.jwt import create_access_token
from app.auth.security import hash_password

from tests.test_authorization import (
    create_test_user,
    delete_test_user,
)


client = TestClient(app)


# ============================================================
# DELIVERY TEST FIXTURES
# ============================================================

def create_test_customer():
    """
    Create a temporary customer for delivery tests.
    """
    db = SessionLocal()

    try:
        customer = Customer(
            name=f"Delivery Test Customer {uuid.uuid4().hex[:8]}",
            phone=f"07{uuid.uuid4().int % 100000000:08d}",
            address="Delivery Test Address",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

        return customer_id

    finally:
        db.close()


def create_test_product():
    """
    Create a temporary product with enough stock for delivery tests.
    """
    db = SessionLocal()

    try:
        product = Product(
            name=f"Delivery Test Product {uuid.uuid4().hex[:8]}",
            category="Test",
            price=Decimal("100.00"),
            stock_quantity=10,
            is_active=True,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        product_id = product.id

        return product_id

    finally:
        db.close()


def create_test_rider():
    """
    Create a temporary rider specifically for delivery tests.
    """
    return create_test_user(UserRole.RIDER)


def create_test_order(rider_id, customer_id, product_id):
    """
    Create a temporary order and order item.
    Reduces product stock by one.
    """
    db = SessionLocal()

    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        assert product is not None

        original_stock = product.stock_quantity

        order = Order(
            customer_id=customer_id,
            created_by=rider_id,
            delivery_address="Delivery Test Address",
            total_amount=Decimal(str(product.price)),
            status=OrderStatus.PENDING.value,
        )

        db.add(order)
        db.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            subtotal=product.price,
        )

        db.add(order_item)

        product.stock_quantity -= 1

        db.commit()
        db.refresh(order)

        return order.id, original_stock

    finally:
        db.close()


def create_delivery_test_data():
    """
    Create everything required for a delivery test.

    Returns:
        customer_id,
        product_id,
        rider_id,
        order_id,
        original_stock
    """
    customer_id = create_test_customer()
    product_id = create_test_product()
    rider = create_test_rider()

    try:
        order_id, original_stock = create_test_order(
            rider_id=rider.id,
            customer_id=customer_id,
            product_id=product_id,
        )

        return (
            customer_id,
            product_id,
            rider.id,
            order_id,
            original_stock,
        )

    except Exception:
        delete_test_user(rider.id)
        raise


def get_test_order_and_rider():
    """
    Backward-compatible helper used by the existing delivery tests.

    Creates its own customer, product, rider and order instead of
    depending on records already existing in the database.

    Returns:
        order_id,
        rider_id,
        original_stock
    """
    customer_id = create_test_customer()
    product_id = create_test_product()
    rider = create_test_rider()

    try:
        order_id, original_stock = create_test_order(
            rider_id=rider.id,
            customer_id=customer_id,
            product_id=product_id,
        )

        return order_id, rider.id, original_stock

    except Exception:
        delete_test_user(rider.id)
        raise


def cleanup_delivery_test(
    order_id,
    original_stock,
    customer_id=None,
    product_id=None,
    rider_id=None,
):
    """
    Completely remove data created by a delivery test.
    """
    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # Find delivery
        # ----------------------------------------------------
        delivery = (
            db.query(Delivery)
            .filter(Delivery.order_id == order_id)
            .first()
        )

        if delivery:
            # Delete status history first because it references
            # the delivery.
            db.query(DeliveryStatusHistory).filter(
                DeliveryStatusHistory.delivery_id == delivery.id
            ).delete(
                synchronize_session=False
            )

            db.delete(delivery)
            db.flush()

        # ----------------------------------------------------
        # Restore stock
        # ----------------------------------------------------
        order = (
            db.query(Order)
            .filter(Order.id == order_id)
            .first()
        )

        if order:
            order_items = (
                db.query(OrderItem)
                .filter(OrderItem.order_id == order_id)
                .all()
            )

            if original_stock is not None:
                for item in order_items:
                    product = (
                        db.query(Product)
                        .filter(Product.id == item.product_id)
                        .first()
                    )

                    if product:
                        product.stock_quantity = original_stock

            # Delete order items before deleting order.
            db.query(OrderItem).filter(
                OrderItem.order_id == order_id
            ).delete(
                synchronize_session=False
            )

            db.delete(order)

        db.commit()

    finally:
        db.close()

    # --------------------------------------------------------
    # Delete temporary customer
    # --------------------------------------------------------
    if customer_id is not None:
        db = SessionLocal()

        try:
            customer = (
                db.query(Customer)
                .filter(Customer.id == customer_id)
                .first()
            )

            if customer:
                db.delete(customer)
                db.commit()

        finally:
            db.close()

    # --------------------------------------------------------
    # Delete temporary product
    # --------------------------------------------------------
    if product_id is not None:
        db = SessionLocal()

        try:
            product = (
                db.query(Product)
                .filter(Product.id == product_id)
                .first()
            )

            if product:
                db.delete(product)
                db.commit()

        finally:
            db.close()

    # --------------------------------------------------------
    # Delete temporary rider
    # --------------------------------------------------------
    if rider_id is not None:
        delete_test_user(rider_id)


def test_dispatcher_can_create_delivery():
    db = SessionLocal()

    dispatcher = create_test_user(UserRole.DISPATCHER)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        token = create_access_token(
            user_id=dispatcher.id,
            role=dispatcher.role.value,
        )

        response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["order_id"] == order_id
        assert data["rider_id"] == rider_id

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(dispatcher.id)


def test_attendant_cannot_create_delivery():
    db = SessionLocal()

    attendant = create_test_user(UserRole.ATTENDANT)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        token = create_access_token(
            user_id=attendant.id,
            role=attendant.role.value,
        )

        response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(attendant.id)


def test_rider_cannot_create_delivery():
    db = SessionLocal()

    rider = create_test_user(UserRole.RIDER)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        token = create_access_token(
            user_id=rider.id,
            role=rider.role.value,
        )

        response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 403

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(rider.id)


def test_admin_can_update_delivery_status():
    db = SessionLocal()

    admin = create_test_user(UserRole.ADMIN)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        create_token = create_access_token(
            user_id=admin.id,
            role=admin.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={
                "Authorization": f"Bearer {create_token}"
            },
        )

        assert create_response.status_code == 201

        delivery_id = create_response.json()["id"]

        # Must progress through the real sequence: ASSIGNED is set by
        # create_delivery, so the next valid step is PICKED_UP, then
        # OUT_FOR_DELIVERY, then DELIVERED.

        picked_up_response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "PICKED_UP"},
            headers={"Authorization": f"Bearer {create_token}"},
        )

        assert picked_up_response.status_code == 200
        assert picked_up_response.json()["picked_up_at"] is not None

        out_for_delivery_response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "OUT_FOR_DELIVERY"},
            headers={"Authorization": f"Bearer {create_token}"},
        )

        assert out_for_delivery_response.status_code == 200
        assert out_for_delivery_response.json()["out_for_delivery_at"] is not None

        response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={
                "status": "DELIVERED",
                "proof_of_delivery": "Customer received order",
            },
            headers={
                "Authorization": f"Bearer {create_token}"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["delivered_at"] is not None
        assert data["proof_of_delivery"] == "Customer received order"

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(admin.id)


def test_delivery_status_cannot_skip_steps():
    db = SessionLocal()

    admin = create_test_user(UserRole.ADMIN)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        token = create_access_token(
            user_id=admin.id,
            role=admin.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert create_response.status_code == 201

        delivery_id = create_response.json()["id"]

        # Delivery is ASSIGNED at this point. Jumping straight to
        # DELIVERED (skipping PICKED_UP and OUT_FOR_DELIVERY) must be
        # rejected.

        response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "DELIVERED"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400

        get_after = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "PICKED_UP"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert get_after.status_code == 200

        # Going backward should also be rejected.

        backward_response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "PICKED_UP"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert backward_response.status_code == 400

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(admin.id)


def test_rider_can_update_own_delivery():
    db = SessionLocal()

    dispatcher = create_test_user(UserRole.DISPATCHER)
    rider = create_test_user(UserRole.RIDER)

    try:
        order_id, _, original_stock = get_test_order_and_rider()

        assert order_id is not None

        dispatcher_token = create_access_token(
            user_id=dispatcher.id,
            role=dispatcher.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider.id,
            },
            headers={
                "Authorization": f"Bearer {dispatcher_token}"
            },
        )

        assert create_response.status_code == 201

        delivery_id = create_response.json()["id"]

        rider_token = create_access_token(
            user_id=rider.id,
            role=rider.role.value,
        )

        response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={
                "status": "PICKED_UP"
            },
            headers={
                "Authorization": f"Bearer {rider_token}"
            },
        )

        assert response.status_code == 200
        assert response.json()["picked_up_at"] is not None

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(dispatcher.id)
        delete_test_user(rider.id)


def test_invalid_delivery_status_rejected():
    db = SessionLocal()

    admin = create_test_user(UserRole.ADMIN)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        token = create_access_token(
            user_id=admin.id,
            role=admin.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert create_response.status_code == 201

        delivery_id = create_response.json()["id"]

        response = client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={
                "status": "INVALID_STATUS"
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code in (400, 422)

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(admin.id)


def test_admin_can_list_deliveries():
    db = SessionLocal()

    admin = create_test_user(UserRole.ADMIN)

    try:
        order_id, rider_id, original_stock = get_test_order_and_rider()

        assert order_id is not None
        assert rider_id is not None

        token = create_access_token(
            user_id=admin.id,
            role=admin.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_response.status_code == 201

        list_response = client.get(
            "/api/deliveries",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200

        ids = [d["id"] for d in list_response.json()]

        assert create_response.json()["id"] in ids

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(admin.id)


def test_rider_cannot_list_all_deliveries():
    db = SessionLocal()

    rider = create_test_user(UserRole.RIDER)

    try:
        token = create_access_token(
            user_id=rider.id,
            role=rider.role.value,
        )

        response = client.get(
            "/api/deliveries",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    finally:
        delete_test_user(rider.id)


def test_rider_can_view_own_delivery_by_id():
    db = SessionLocal()

    dispatcher = create_test_user(UserRole.DISPATCHER)
    rider = create_test_user(UserRole.RIDER)

    try:
        order_id, _, original_stock = get_test_order_and_rider()

        assert order_id is not None

        dispatcher_token = create_access_token(
            user_id=dispatcher.id,
            role=dispatcher.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider.id,
            },
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )

        assert create_response.status_code == 201

        delivery_id = create_response.json()["id"]

        rider_token = create_access_token(
            user_id=rider.id,
            role=rider.role.value,
        )

        response = client.get(
            f"/api/deliveries/{delivery_id}",
            headers={"Authorization": f"Bearer {rider_token}"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == delivery_id

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(dispatcher.id)
        delete_test_user(rider.id)


def test_rider_cannot_view_another_riders_delivery():
    db = SessionLocal()

    dispatcher = create_test_user(UserRole.DISPATCHER)
    rider = create_test_user(UserRole.RIDER)
    other_rider = create_test_user(UserRole.RIDER)

    try:
        order_id, _, original_stock = get_test_order_and_rider()

        assert order_id is not None

        dispatcher_token = create_access_token(
            user_id=dispatcher.id,
            role=dispatcher.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider.id,
            },
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )

        assert create_response.status_code == 201

        delivery_id = create_response.json()["id"]

        other_rider_token = create_access_token(
            user_id=other_rider.id,
            role=other_rider.role.value,
        )

        response = client.get(
            f"/api/deliveries/{delivery_id}",
            headers={"Authorization": f"Bearer {other_rider_token}"},
        )

        assert response.status_code == 403

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(dispatcher.id)
        delete_test_user(rider.id)
        delete_test_user(other_rider.id)


def test_rider_can_list_own_deliveries_via_mine():
    db = SessionLocal()

    dispatcher = create_test_user(UserRole.DISPATCHER)
    rider = create_test_user(UserRole.RIDER)

    try:
        order_id, _, original_stock = get_test_order_and_rider()

        assert order_id is not None

        dispatcher_token = create_access_token(
            user_id=dispatcher.id,
            role=dispatcher.role.value,
        )

        create_response = client.post(
            "/api/deliveries",
            json={
                "order_id": order_id,
                "rider_id": rider.id,
            },
            headers={"Authorization": f"Bearer {dispatcher_token}"},
        )

        assert create_response.status_code == 201

        rider_token = create_access_token(
            user_id=rider.id,
            role=rider.role.value,
        )

        mine_response = client.get(
            "/api/deliveries/mine",
            headers={"Authorization": f"Bearer {rider_token}"},
        )

        assert mine_response.status_code == 200

        data = mine_response.json()

        assert all(d["rider_id"] == rider.id for d in data)
        assert create_response.json()["id"] in [d["id"] for d in data]

        cleanup_delivery_test(
            order_id,
            original_stock,
        )

    finally:
        delete_test_user(dispatcher.id)
        delete_test_user(rider.id)


def test_mine_route_not_shadowed_by_delivery_id_route():
    # Regression guard: "/mine" must resolve to the dedicated route, not be
    # swallowed by "/{delivery_id}" (which would try to parse "mine" as an
    # int and return 422 instead of a real result).
    db = SessionLocal()

    rider = create_test_user(UserRole.RIDER)

    try:
        token = create_access_token(
            user_id=rider.id,
            role=rider.role.value,
        )

        response = client.get(
            "/api/deliveries/mine",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    finally:
        delete_test_user(rider.id)