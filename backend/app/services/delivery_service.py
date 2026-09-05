from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.delivery import Delivery
from app.models.delivery_status_history import DeliveryStatusHistory
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from app.models.user import User
from app.schemas.delivery import DeliveryCreate, DeliveryStatusUpdate


# Each entry maps a delivery's current status to the single status it is
# allowed to move to next. CANCELLED is intentionally not included here —
# cancellation is out of scope for Step 8 and is handled separately at the
# order level.
VALID_STATUS_TRANSITIONS = {
    OrderStatus.ASSIGNED: OrderStatus.PICKED_UP,
    OrderStatus.PICKED_UP: OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.OUT_FOR_DELIVERY: OrderStatus.DELIVERED,
}


def list_deliveries(db: Session) -> list[Delivery]:
    return (
        db.query(Delivery)
        .order_by(Delivery.created_at.desc())
        .all()
    )


def get_delivery(
    db: Session,
    delivery_id: int,
    current_user: User,
) -> Delivery:
    delivery = (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id)
        .first()
    )

    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    if (
        current_user.role == UserRole.RIDER
        and delivery.rider_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Riders can only view their own deliveries",
        )

    return delivery


def get_my_deliveries(
    db: Session,
    current_user: User,
) -> list[Delivery]:
    return (
        db.query(Delivery)
        .filter(Delivery.rider_id == current_user.id)
        .order_by(Delivery.created_at.desc())
        .all()
    )


def create_delivery(
    db: Session,
    delivery_data: DeliveryCreate,
    current_user: User,
) -> Delivery:
    # -----------------------------------------------------
    # Verify order exists
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == delivery_data.order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # -----------------------------------------------------
    # Verify rider exists and has RIDER role
    # -----------------------------------------------------

    rider = (
        db.query(User)
        .filter(
            User.id == delivery_data.rider_id,
            User.is_active.is_(True),
        )
        .first()
    )

    if rider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found",
        )

    if rider.role != UserRole.RIDER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not a rider",
        )

    # -----------------------------------------------------
    # Prevent duplicate delivery for an order
    # -----------------------------------------------------

    existing_delivery = (
        db.query(Delivery)
        .filter(Delivery.order_id == delivery_data.order_id)
        .first()
    )

    if existing_delivery is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery already exists for this order",
        )

    # -----------------------------------------------------
    # Create delivery
    # -----------------------------------------------------

    delivery = Delivery(
        order_id=order.id,
        rider_id=rider.id,
        assigned_by=current_user.id,
        assigned_at=datetime.now(timezone.utc),
    )

    db.add(delivery)

    # Update order status
    order.status = OrderStatus.ASSIGNED.value

    db.flush()

    # -----------------------------------------------------
    # Create status history
    # -----------------------------------------------------

    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        status=OrderStatus.ASSIGNED.value,
        updated_by=current_user.id,
        notes="Delivery assigned to rider",
    )

    db.add(history)

    db.commit()
    db.refresh(delivery)

    return delivery


def update_delivery_status(
    db: Session,
    delivery_id: int,
    status_data: DeliveryStatusUpdate,
    current_user: User,
) -> Delivery:
    # -----------------------------------------------------
    # Find delivery
    # -----------------------------------------------------

    delivery = (
        db.query(Delivery)
        .filter(Delivery.id == delivery_id)
        .first()
    )

    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    # -----------------------------------------------------
    # Riders can only update their own deliveries
    # -----------------------------------------------------

    if (
        current_user.role == UserRole.RIDER
        and delivery.rider_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Riders can only update their own deliveries",
        )

    new_status = status_data.status

    # -----------------------------------------------------
    # Look up the related order (needed to know current status)
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == delivery.order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related order not found",
        )

    try:
        current_status = OrderStatus(order.status)
    except ValueError:
        current_status = None

    # -----------------------------------------------------
    # Validate status transition
    # -----------------------------------------------------

    allowed_statuses = {
        OrderStatus.PICKED_UP,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.DELIVERED,
    }

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid delivery status",
        )

    expected_next_status = VALID_STATUS_TRANSITIONS.get(current_status)

    if expected_next_status != new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition delivery from "
                f"{current_status.value if current_status else order.status} "
                f"to {new_status.value} — expected next status is "
                f"{expected_next_status.value if expected_next_status else 'none (terminal or unassigned state)'}"
            ),
        )

    # -----------------------------------------------------
    # Update timestamps
    # -----------------------------------------------------

    now = datetime.now(timezone.utc)

    if new_status == OrderStatus.PICKED_UP:
        delivery.picked_up_at = now

    elif new_status == OrderStatus.OUT_FOR_DELIVERY:
        delivery.out_for_delivery_at = now

    elif new_status == OrderStatus.DELIVERED:
        delivery.delivered_at = now

        if status_data.proof_of_delivery:
            delivery.proof_of_delivery = status_data.proof_of_delivery

    # -----------------------------------------------------
    # Update order status
    # -----------------------------------------------------

    order.status = new_status.value

    # -----------------------------------------------------
    # Record status history
    # -----------------------------------------------------

    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        status=new_status.value,
        updated_by=current_user.id,
        notes=status_data.notes,
    )

    db.add(history)

    db.commit()
    db.refresh(delivery)

    return delivery