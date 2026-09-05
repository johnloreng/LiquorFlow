from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.customer import Customer
from app.models.enums import UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
)


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ATTENDANT,
        )
    ),
):
    # -----------------------------------------------------
    # Verify customer exists
    # -----------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(Customer.id == order_data.customer_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # -----------------------------------------------------
    # Validate products and calculate totals
    # -----------------------------------------------------

    total_amount = Decimal("0.00")
    order_items_data = []

    for item_data in order_data.items:

        product = (
            db.query(Product)
            .filter(
                Product.id == item_data.product_id,
                Product.is_active.is_(True),
            )
            .with_for_update()
            .first()
        )

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Product {item_data.product_id} "
                    "not found or inactive"
                ),
            )

        if product.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for "
                    f"{product.name}. "
                    f"Available: {product.stock_quantity}"
                ),
            )

        unit_price = Decimal(str(product.price))
        subtotal = unit_price * item_data.quantity

        total_amount += subtotal

        order_items_data.append(
            {
                "product": product,
                "quantity": item_data.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    # -----------------------------------------------------
    # Create order
    # -----------------------------------------------------

    order = Order(
        customer_id=customer.id,
        created_by=current_user.id,
        delivery_address=order_data.delivery_address,
        total_amount=total_amount,
        status="PENDING",
    )

    db.add(order)
    db.flush()

    # -----------------------------------------------------
    # Create order items and reduce stock
    # -----------------------------------------------------

    for item_data in order_items_data:

        product = item_data["product"]

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"],
        )

        db.add(order_item)

        product.stock_quantity -= item_data["quantity"]

    # -----------------------------------------------------
    # Commit transaction
    # -----------------------------------------------------

    db.commit()
    db.refresh(order)

    return order

@router.get(
    "",
    response_model=list[OrderResponse],
)
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ATTENDANT,
            UserRole.DISPATCHER,
        )
    ),
):
    return (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
    )