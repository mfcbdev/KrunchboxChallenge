# Venue Tickets

**Live:** _https://YOUR-SERVICE.onrender.com_ (UI at `/`, API docs at `/docs`). Free hosting sleeps when idle, so the first request can take 30–60 s.

A ticketing API for an event venue: **purchase** tickets (capacity goes down) and **refund** them (capacity comes back), without ever overselling, even when many requests hit the same event at once.

Python · FastAPI · SQLAlchemy 2.0 · PostgreSQL (psycopg 3) · pytest · Docker

## Run it

### With Docker (one command)

Requires Docker Desktop, running.

```bash
docker compose up --build
```

Open http://localhost:8000. The app seeds 3 events (one with plenty of seats, one nearly sold out, one already started) and 2 customers on first start.

### Without Docker for the app

Requires [uv](https://docs.astral.sh/uv/) and a Postgres. The easiest Postgres is the one from Compose:

```bash
docker compose up -d db
uv sync
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

The default `DATABASE_URL` is `postgresql+psycopg://tickets:tickets@localhost:5432/tickets`. Set the env var to use another database.

### Tests

```bash
docker compose up -d db
uv run pytest
```

Tests run against real Postgres, in a separate `tickets_test` database (override with `TEST_DATABASE_URL`). They never touch `DATABASE_URL`, so they can't wipe real data.

- `test_purchase.py`: happy path, sold out (409), last seats, quantity validation (422), unknown event or customer (404), purchase after the event started (409).
- `test_refund.py`: refund restores capacity, double refund is 409 and restores only once, unknown order (404), refund after the event started (409).
- `test_concurrency.py`: 20 threads buy the last 5 seats at the same instant: exactly 5 succeed, 15 get 409, `available` ends at 0, 5 orders exist. 10 threads refund the same order at once: exactly 1 succeeds.

## API

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| `GET` | `/events` | | 200 list | |
| `GET` | `/events/{id}` | | 200 | 404 |
| `POST` | `/events/{id}/purchase` | `{"customer_id": 1, "quantity": 2}` (1–10) | **201** order | 404, 409 not enough tickets / event started, 422 |
| `POST` | `/orders/{id}/refund` | | 200 order (`REFUNDED`) | 404, 409 already refunded / event started |
| `GET` | `/customers` | | 200 list | |
| `GET` | `/customers/{id}/orders` | | 200 list | 404 |
| `GET` | `/health` | | 200 | |

Errors are `{"detail": "<reason>"}`. Money is returned as decimal strings (`"35.00"`).

## Data model

```
Event      id, name, venue, starts_at (tz-aware), capacity, available, ticket_price, created_at
           CHECK capacity > 0, CHECK 0 <= available <= capacity
Customer   id, name, email (unique), created_at
Order      id, event_id → Event, customer_id → Customer, quantity, unit_price, status (PAID | REFUNDED),
           created_at, refunded_at
           CHECK quantity > 0, indexes on event_id and customer_id
```

One `Order` row per purchase with a `quantity`, not one row per ticket. Refunds are whole orders. `total` is computed (`quantity × unit_price`), never stored.

## Code layout

```
app/
  main.py      routes, domain error → HTTP status, serves the UI
  services.py  purchase_tickets(), refund_order(): all business logic, no HTTP
  models.py    SQLAlchemy models and CHECK constraints
  schemas.py   Pydantic request/response models
  database.py  engine, session, get_db dependency
  seed.py      demo data (skips if data exists)
  static/index.html   one-page UI, vanilla JS, no build step
tests/
```

Routes stay thin: validate, call a service, map `NotFound` → 404 and `Conflict` → 409.

## Design decisions

**Purchase is one conditional `UPDATE`.** The whole problem is the race: two buyers read "1 seat left" and both buy it. Instead of read-then-write, the purchase is a single statement:

```sql
UPDATE events SET available = available - :q
WHERE id = :id AND available >= :q AND starts_at > now()
RETURNING ticket_price
```

Postgres locks the row while it checks the condition, and a concurrent update re-checks it after waiting. Zero rows back means sold out (or not found / already started), so overselling is impossible without any application-level lock. The order is inserted in the same transaction, so a failed insert rolls the seats back.

**Refund locks the order row.** `SELECT ... FOR UPDATE` on the order, then check its status. Two refunds of the same order run one after the other; the second sees `REFUNDED` and returns 409, so capacity is restored exactly once. The capacity increment is itself an atomic `available = available + q`.

**CHECK constraints in the database.** `0 <= available <= capacity` and `quantity > 0` hold even if a future code path is wrong. The service logic is the first line of defense; the database is the last.

**`Numeric(10, 2)` and `Decimal` for money, never float.** Each order stores `unit_price` as a snapshot, so a later price change never rewrites past orders.

**Sync SQLAlchemy sessions.** FastAPI runs sync endpoints in a thread pool, which is simpler than async and correct here; the database is what serializes the contended work.

**Refunds close when the event starts,** and so do sales. Both return 409 with the reason.

## What I'd add next

- **Auth**, so customers can only see and refund their own orders.
- **Alembic** migrations instead of `create_all()` on startup.
- **Idempotency keys** on purchase, so a retried request (network blip, double submit) can't create two orders.
- **Per-ticket records with QR codes** for entry scanning, on top of the order.
- **Pagination** on the list endpoints.

## Deploy

Render (app, from the `Dockerfile`) + Neon (Postgres). Step by step in [DEPLOY.md](DEPLOY.md).
