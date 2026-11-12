---
version: 1
slug: "app-static-index-html"
primary_target: "app/static/index.html"
related_targets: []
---

# Surface: Venue Tickets console (app/static/index.html)

Mode: Operate. Audience: challenge reviewer verifying purchase/refund rules in under a minute. Code-led (no image generation). World pinned by the user's brief (Krunchbox visual language, renamed "Venue Tickets").

## Direction contract

THESIS: A one-page box-office console where every rule the backend enforces is visible: seats drop on purchase, return on refund, refusals shown inline with the server's reason. Refuses the dashboard-of-tiles default and any modal or alert().

OWN-WORLD: White ground, #F5F5F5 band behind the events, white cards with #E5E5E5 hairlines, 10px card radius, 7px controls. Figtree 700 navy #04334D headings and buttons, DM Sans 400 #4B4F58 body. Cyan #00ADEE CTA with navy label (AA decision, user-confirmed). Green #2ABB7F / orange #F8A03F only as dots and meter fills, never as text.

STORY: Pick who is buying, see seats left per event, buy, watch the meter fall; refund from the orders table, watch it rise; hit a rule and read why.

FIRST VIEWPORT: Header row: product name left, "Buying as" customer select right. Below, the events band: three cards side by side (name, date and venue, price, seat meter "97 / 100 left", quantity + Buy). Orders table begins under the fold on laptops.

FORM: Pinned by brief (no roll). Signature move: the seat meter animates to its new value after each purchase/refund. seed: none (pinned by brief, no roll)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
