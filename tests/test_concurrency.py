"""Many requests hit the same row at the same instant. The DB, not luck, decides who wins."""

import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app import services
from app.database import DATABASE_URL, SessionLocal
from app.models import Order
from tests.conftest import available


def run_at_once(n: int, fn) -> list[str]:
    """Run fn(session) in n threads released together; return 'ok' / 'conflict' per thread."""
    # One connection per thread so nobody queues on the pool instead of on the database.
    engine = create_engine(DATABASE_URL, pool_size=n)
    Session = sessionmaker(engine, expire_on_commit=False)
    barrier = threading.Barrier(n)

    def worker(_):
        with Session() as db:
            db.connection()  # check out the connection before the race starts
            barrier.wait()
            try:
                fn(db)
                return "ok"
            except services.Conflict:
                return "conflict"

    try:
        with ThreadPoolExecutor(max_workers=n) as pool:
            return list(pool.map(worker, range(n)))
    finally:
        engine.dispose()


def test_parallel_purchases_never_oversell(make_event, customer):
    event = make_event(capacity=5)

    results = run_at_once(20, lambda db: services.purchase_tickets(db, event.id, customer.id, 1))

    assert results.count("ok") == 5
    assert results.count("conflict") == 15
    assert available(event.id) == 0
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 5


def test_parallel_refunds_of_one_order_succeed_once(make_event, customer):
    event = make_event(capacity=10)
    with SessionLocal() as db:
        order = services.purchase_tickets(db, event.id, customer.id, 3)
    assert available(event.id) == 7

    results = run_at_once(10, lambda db: services.refund_order(db, order.id))

    assert results.count("ok") == 1
    assert results.count("conflict") == 9
    assert available(event.id) == 10
