from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryStatusUpdate,
)
from app.services import delivery_service


router = APIRouter(
    prefix="/api/deliveries",
    tags=["Deliveries"],
)


@router.get(
    "",
    response_model=list[DeliveryResponse],
)
def list_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.DISPATCHER,
        )
    ),
):
    return delivery_service.list_deliveries(db=db)


@router.get(
    "/mine",
    response_model=list[DeliveryResponse],
)
def get_my_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.RIDER,
        )
    ),
):
    return delivery_service.get_my_deliveries(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
)
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.DISPATCHER,
            UserRole.RIDER,
        )
    ),
):
    return delivery_service.get_delivery(
        db=db,
        delivery_id=delivery_id,
        current_user=current_user,
    )


@router.post(
    "",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_delivery(
    delivery_data: DeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.DISPATCHER,
        )
    ),
):
    return delivery_service.create_delivery(
        db=db,
        delivery_data=delivery_data,
        current_user=current_user,
    )


@router.patch(
    "/{delivery_id}/status",
    response_model=DeliveryResponse,
)
def update_delivery_status(
    delivery_id: int,
    status_data: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.RIDER,
        )
    ),
):
    return delivery_service.update_delivery_status(
        db=db,
        delivery_id=delivery_id,
        status_data=status_data,
        current_user=current_user,
    )