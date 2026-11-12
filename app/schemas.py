from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import OrderStatus


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    venue: str
    starts_at: datetime
    capacity: int
    available: int
    ticket_price: Decimal


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class PurchaseIn(BaseModel):
    customer_id: int
    quantity: int = Field(ge=1, le=10)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    customer_id: int
    quantity: int
    unit_price: Decimal
    total: Decimal
    status: OrderStatus
    created_at: datetime
    refunded_at: datetime | None
