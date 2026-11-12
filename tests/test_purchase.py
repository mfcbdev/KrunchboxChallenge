from datetime import timedelta

import pytest

from tests.conftest import available


def test_purchase_reduces_capacity_and_snapshots_price(client, make_event, customer):
    event = make_event(capacity=100, price="35.50")

    r = client.post(f"/events/{event.id}/purchase", json={"customer_id": customer.id, "quantity": 3})

    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "PAID"
    assert order["quantity"] == 3
    assert order["unit_price"] == "35.50"
    assert order["total"] == "106.50"
    assert available(event.id) == 97


def test_sold_out_is_409_and_capacity_untouched(client, make_event, customer):
    event = make_event(capacity=10, available=2)

    r = client.post(f"/events/{event.id}/purchase", json={"customer_id": customer.id, "quantity": 3})

    assert r.status_code == 409
    assert available(event.id) == 2


def test_can_buy_the_last_seats_exactly(client, make_event, customer):
    event = make_event(capacity=10, available=2)

    r = client.post(f"/events/{event.id}/purchase", json={"customer_id": customer.id, "quantity": 2})

    assert r.status_code == 201
    assert available(event.id) == 0


@pytest.mark.parametrize("quantity", [0, -1, 11, "two"])
def test_invalid_quantity_is_422(client, make_event, customer, quantity):
    event = make_event()

    r = client.post(f"/events/{event.id}/purchase", json={"customer_id": customer.id, "quantity": quantity})

    assert r.status_code == 422
    assert available(event.id) == 100


def test_unknown_event_is_404(client, customer):
    r = client.post("/events/999/purchase", json={"customer_id": customer.id, "quantity": 1})
    assert r.status_code == 404


def test_unknown_customer_is_404(client, make_event):
    event = make_event()

    r = client.post(f"/events/{event.id}/purchase", json={"customer_id": 999, "quantity": 1})

    assert r.status_code == 404
    assert available(event.id) == 100


def test_purchase_after_event_start_is_409(client, make_event, customer):
    event = make_event(starts_in=timedelta(hours=-1))

    r = client.post(f"/events/{event.id}/purchase", json={"customer_id": customer.id, "quantity": 1})

    assert r.status_code == 409
    assert available(event.id) == 100


def test_ui_is_served_at_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Venue Tickets" in r.text
