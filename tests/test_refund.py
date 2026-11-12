from datetime import UTC, datetime, timedelta

from app.database import SessionLocal
from app.models import Event
from tests.conftest import available


def buy(client, event_id, customer_id, quantity=2) -> dict:
    r = client.post(f"/events/{event_id}/purchase", json={"customer_id": customer_id, "quantity": quantity})
    assert r.status_code == 201
    return r.json()


def test_refund_restores_capacity(client, make_event, customer):
    event = make_event(capacity=10)
    order = buy(client, event.id, customer.id, quantity=4)
    assert available(event.id) == 6

    r = client.post(f"/orders/{order['id']}/refund")

    assert r.status_code == 200
    assert r.json()["status"] == "REFUNDED"
    assert r.json()["refunded_at"] is not None
    assert available(event.id) == 10


def test_double_refund_is_409_and_restores_once(client, make_event, customer):
    event = make_event(capacity=10)
    order = buy(client, event.id, customer.id, quantity=4)

    assert client.post(f"/orders/{order['id']}/refund").status_code == 200
    assert client.post(f"/orders/{order['id']}/refund").status_code == 409
    assert available(event.id) == 10


def test_unknown_order_is_404(client):
    assert client.post("/orders/999/refund").status_code == 404


def test_refund_after_event_start_is_409(client, make_event, customer):
    event = make_event(capacity=10)
    order = buy(client, event.id, customer.id)
    with SessionLocal() as db:  # the event starts after the purchase
        db.get(Event, event.id).starts_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()

    r = client.post(f"/orders/{order['id']}/refund")

    assert r.status_code == 409
    assert available(event.id) == 8


def test_customer_orders_lists_both_states(client, make_event, customer):
    event = make_event()
    first = buy(client, event.id, customer.id)
    buy(client, event.id, customer.id)
    client.post(f"/orders/{first['id']}/refund")

    r = client.get(f"/customers/{customer.id}/orders")

    assert r.status_code == 200
    assert sorted(o["status"] for o in r.json()) == ["PAID", "REFUNDED"]
