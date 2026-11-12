# Deploy: Render (app) + Neon (Postgres)

You never run Docker yourself: Render builds the `Dockerfile` from GitHub. The container seeds demo data on first start (the seed skips if events already exist), so there is no manual seed step.

Both services have free tiers. Limits change, so check the current ones on each pricing page before relying on them.

## 1. Push the repo to GitHub

```bash
git init
git add .
git commit -m "Venue Tickets"
```

Create an empty repository on github.com (no README), then:

```bash
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

## 2. Create the database on Neon

1. Sign in at neon.tech and click **New Project**.
2. Name it `venue-tickets`, region **AWS US West 2 (Oregon)** (same region as the Render service in `render.yaml`), Postgres 16 or newer. Click **Create**.
3. On the project dashboard click **Connect**. Turn **Connection pooling off** to get the *direct* URL (its host has no `-pooler`). The refund uses `SELECT ... FOR UPDATE`, which is safest on a direct connection.
4. Copy the connection string. It looks like:
   `postgresql://user:pass@ep-xxx.us-west-2.aws.neon.tech/neondb?sslmode=require`
5. Change the scheme so SQLAlchemy uses psycopg 3: replace `postgresql://` with `postgresql+psycopg://`. Keep the `?sslmode=require` part.

## 3. Create the web service on Render

1. Sign in at render.com and click **New → Blueprint**.
2. Connect your GitHub account if asked, then pick the repository. Render reads `render.yaml` and shows one service, `venue-tickets`.
3. It asks for `DATABASE_URL`: paste the `postgresql+psycopg://...` URL from step 2.
4. Click **Apply** (or **Deploy Blueprint**). The first build takes a few minutes.
5. When the deploy log shows `Seeded 3 events and 2 customers.` and the service turns **Live**, open the URL at the top of the service page (`https://venue-tickets-xxxx.onrender.com`).

Check it: `/health` returns `{"status":"ok"}`, `/` shows the UI, `/docs` shows the API.

## 4. Put the live URL in the README

Add the URL as the first line of `README.md` (written in Phase 6) and push. Every push to `main` redeploys automatically.

## Good to know

- **Cold starts:** free Render services sleep when idle. The first request after a while can take 30–60 s; the UI says so while it waits.
- **Reset the demo data:** in the Neon SQL editor run `TRUNCATE orders, customers, events RESTART IDENTITY;`, then in Render click **Manual Deploy → Restart service**. The seed runs again on start.
- **Deploy fails with `No module named 'psycopg2'`** (URL starts with `postgresql://`) **or `Can't load plugin: sqlalchemy.dialects:postgres`** (URL starts with `postgres://`): the scheme was not changed. Set it to `postgresql+psycopg://` in Render → **Environment**, then redeploy.
- **Alternative to Neon:** Supabase works too. Use its direct or *session* pooler URL, never the transaction pooler (port 6543), which breaks prepared statements and row locks.
