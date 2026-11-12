# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static: one `app/static/index.html` with plain HTML, CSS and vanilla JS (`fetch`), no framework, no build step, served by FastAPI at `/`. Decided in PLAN.md.

## Users

Primarily the reviewer of the Krunchbox backend challenge: someone evaluating the ticketing API who wants to exercise purchase and refund quickly and see the rules hold (sold out, already refunded, event started). The fiction on screen is an internal venue console where an operator picks a customer and buys or refunds on their behalf.

## Product Purpose

Venue Tickets sells tickets for venue events and refunds them, never overselling capacity. The UI exists to make the backend's behavior visible: capacity going down on purchase, back up on refund, and clear refusals (HTTP 409) when a rule blocks an action. Success: a reviewer understands and verifies the purchase/refund rules within a minute, without reading the API docs.

## Positioning

The backend is what is graded. The guarantees are enforced in Postgres (atomic conditional update, row lock on refund, CHECK constraints), and the UI should surface those outcomes plainly rather than hide them.

## Operating Context

Opened in a desktop browser, often next to `/docs` or the README. Seed data: 3 events (one plenty of seats, one nearly sold out, one already started) and 2 customers. Free hosting may cold-start for 30–60 s on first request.

## Capabilities and Constraints

- API: `GET /events`, `GET /customers`, `GET /customers/{id}/orders`, `POST /events/{id}/purchase` `{customer_id, quantity 1–10}`, `POST /orders/{id}/refund`.
- Errors return `{"detail": "..."}`: 404 not found, 409 conflict (not enough tickets, event started, already refunded), 422 validation.
- Refunds are whole orders. Money is decimal strings (e.g. "35.00").
- No auth, no customer creation, no event management. The UI must never add backend complexity; one page only.

## Brand Commitments

- Name on screen: "Venue Tickets". Do not use the Krunchbox name or logo.
- Visual language matches Krunchbox's, as specified by the user: Figtree 700 (headings, buttons), DM Sans 400 (body); navy #04334D headings, #4B4F58 body text, #0170B9 links/primary; CTA cyan #00ADEE with white text, 7px radius, 8px 12px padding; #FFFFFF background, #F5F5F5 surface, #E5E5E5 borders; success #2ABB7F, warning #F8A03F.
- Tone: confident, plain language, no jargon. Minimal, lots of white space.

## Evidence on Hand

Only the seed data in `app/seed.py`. No real events, customers, testimonials or metrics; do not invent any.

## Product Principles

1. Show the rule, don't hide it: every refusal is shown inline with the server's reason.
2. State after every action is fresh from the server, never guessed client-side.
3. One page, scannable in seconds.
4. The UI adds no backend surface beyond what the API already offers.

## Accessibility & Inclusion

WCAG 2.2 AA: text contrast, full keyboard use, visible focus, labelled controls, errors announced via live regions, respects reduced motion.
