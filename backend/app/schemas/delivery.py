from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import OrderStatus


class DeliveryCreate(BaseModel):
    order_id: int
    rider_id: int


class DeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    rider_id: int | None
    assigned_by: int | None
    assigned_at: datetime | None
    picked_up_at: datetime | None
    out_for_delivery_at: datetime | None
    delivered_at: datetime | None
    proof_of_delivery: str | None
    created_at: datetime
    updated_at: datetime


class DeliveryStatusUpdate(BaseModel):
    status: OrderStatus
    proof_of_delivery: str | None = None
    notes: str | None = None