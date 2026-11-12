from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import services
from app.database import Base, engine, get_db
from app.models import Customer, Event, Order
from app.schemas import CustomerOut, EventOut, OrderOut, PurchaseIn


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # a real project would use Alembic migrations
    yield


app = FastAPI(title="Venue Tickets", lifespan=lifespan)

Db = Annotated[Session, Depends(get_db)]


@app.exception_handler(services.NotFound)
def not_found(_: Request, exc: services.NotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(services.Conflict)
def conflict(_: Request, exc: services.Conflict) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/events", response_model=list[EventOut])
def list_events(db: Db):
    return db.scalars(select(Event).order_by(Event.starts_at)).all()


@app.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Db):
    event = db.get(Event, event_id)
    if event is None:
        raise services.NotFound("Event not found")
    return event


@app.post("/events/{event_id}/purchase", response_model=OrderOut, status_code=201)
def purchase(event_id: int, body: PurchaseIn, db: Db):
    return services.purchase_tickets(db, event_id, body.customer_id, body.quantity)


@app.post("/orders/{order_id}/refund", response_model=OrderOut)
def refund(order_id: int, db: Db):
    return services.refund_order(db, order_id)


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Db):
    return db.scalars(select(Customer).order_by(Customer.id)).all()


@app.get("/customers/{customer_id}/orders", response_model=list[OrderOut])
def customer_orders(customer_id: int, db: Db):
    if db.get(Customer, customer_id) is None:
        raise services.NotFound("Customer not found")
    return db.scalars(select(Order).where(Order.customer_id == customer_id).order_by(Order.id.desc())).all()


# Mounted last so the API routes above take precedence; serves the UI at "/".
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")
