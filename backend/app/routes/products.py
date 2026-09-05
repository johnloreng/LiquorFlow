from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.enums import UserRole
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductStatusUpdate,
)


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


# -----------------------------------------------------
# List products
# -----------------------------------------------------

@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ATTENDANT,
            UserRole.DISPATCHER,
            UserRole.RIDER,
        )
    ),
):
    query = db.query(Product)

    if is_active is not None:
        query = query.filter(
            Product.is_active.is_(is_active)
        )

    return query.order_by(Product.name.asc()).all()


# -----------------------------------------------------
# Get product by ID
# -----------------------------------------------------

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ATTENDANT,
            UserRole.DISPATCHER,
            UserRole.RIDER,
        )
    ),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


# -----------------------------------------------------
# Create product
# -----------------------------------------------------

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    product = Product(
        name=product_data.name,
        category=product_data.category,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
        is_active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# -----------------------------------------------------
# Update product
# -----------------------------------------------------

@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


# -----------------------------------------------------
# Deactivate product
# -----------------------------------------------------

@router.patch(
    "/{product_id}/deactivate",
    response_model=ProductResponse,
)
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.is_active = False

    db.commit()
    db.refresh(product)

    return product

# -----------------------------------------------------
# Change product status
# -----------------------------------------------------

@router.patch(
    "/{product_id}/status",
    response_model=ProductResponse,
)
def change_product_status(
    product_id: int,
    status_data: ProductStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.is_active = status_data.is_active

    db.commit()
    db.refresh(product)

    return product