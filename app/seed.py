"""Demo data. Safe to run on every start: does nothing if events already exist."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Customer, Event


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Event.id).limit(1)) is not None:
            print("Seed skipped: data already present.")
            return
        now = datetime.now(UTC)
        db.add_all(
            [
                Event(
                    name="Jazz Night",
                    venue="Main Hall",
                    starts_at=now + timedelta(days=14),
                    capacity=100,
                    available=100,
                    ticket_price=Decimal("35.00"),
                ),
                Event(
                    name="Indie Showcase",
                    venue="Studio B",
                    starts_at=now + timedelta(days=3),
                    capacity=50,
                    available=3,  # nearly sold out
                    ticket_price=Decimal("20.00"),
                ),
                Event(
                    name="Morning Talk",
                    venue="Lobby Stage",
                    starts_at=now - timedelta(hours=1),  # already started
                    capacity=40,
                    available=12,
                    ticket_price=Decimal("10.00"),
                ),
                Customer(name="Ada Lovelace", email="ada@example.com"),
                Customer(name="Grace Hopper", email="grace@example.com"),
            ]
        )
        db.commit()
        print("Seeded 3 events and 2 customers.")


if __name__ == "__main__":
    seed()
