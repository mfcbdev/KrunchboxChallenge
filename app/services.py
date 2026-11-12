"""Business logic. Knows nothing about HTTP; raises domain errors that main.py maps to status codes."""

from datetime import UTC, datetime

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.models import Customer, Event, Order, OrderStatus


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


def purchase_tickets(db: Session, event_id: int, customer_id: int, quantity: int) -> Order:
    if db.get(Customer, customer_id) is None:
        raise NotFound("Customer not found")

    # One atomic conditional UPDATE: Postgres row-locks the event while checking `available`,
    # so concurrent buyers can never oversell. No rows back means the condition failed.
    row = db.execute(
        update(Event)
        .where(Event.id == event_id, Event.available >= quantity, Event.starts_at > func.now())
        .values(available=Event.available - quantity)
        .returning(Event.ticket_price)
    ).first()

    if row is None:
        event = db.get(Event, event_id)
        if event is None:
            raise NotFound("Event not found")
        if event.starts_at <= datetime.now(UTC):
            raise Conflict("This event has already started")
        raise Conflict(f"Not enough tickets left (only {event.available} available)")

    order = Order(event_id=event_id, customer_id=customer_id, quantity=quantity, unit_price=row.ticket_price)
    db.add(order)
    db.commit()
    return order


def refund_order(db: Session, order_id: int) -> Order:
    # Lock the order row so two refunds of the same order run one after the other;
    # the second one then sees REFUNDED and stops.
    order = db.get(Order, order_id, with_for_update=True)
    if order is None:
        raise NotFound("Order not found")
    if order.status == OrderStatus.REFUNDED:
        raise Conflict("Order is already refunded")

    event = db.get(Event, order.event_id)
    now = datetime.now(UTC)
    if event.starts_at <= now:
        raise Conflict("Refunds close when the event starts")

    db.execute(
        update(Event).where(Event.id == order.event_id).values(available=Event.available + order.quantity)
    )
    order.status = OrderStatus.REFUNDED
    order.refunded_at = now
    db.commit()
    return order
