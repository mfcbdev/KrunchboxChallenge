import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

# Point the app at a dedicated test database BEFORE importing it: the fixtures below wipe tables,
# so they must never touch whatever DATABASE_URL happens to be set (dev or production data).
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://tickets:tickets@localhost:5432/tickets_test"
)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Customer, Event  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clean_tables():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE orders, customers, events RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def make_event():
    def _make(capacity=100, available=None, starts_in=timedelta(days=7), price="25.00") -> Event:
        with SessionLocal() as db:
            event = Event(
                name="Test Event",
                venue="Hall",
                starts_at=datetime.now(UTC) + starts_in,
                capacity=capacity,
                available=capacity if available is None else available,
                ticket_price=Decimal(price),
            )
            db.add(event)
            db.commit()
            return event

    return _make


@pytest.fixture
def customer() -> Customer:
    with SessionLocal() as db:
        c = Customer(name="Test Buyer", email="buyer@example.com")
        db.add(c)
        db.commit()
        return c


def available(event_id: int) -> int:
    with SessionLocal() as db:
        return db.get(Event, event_id).available
