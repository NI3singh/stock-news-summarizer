# 🚀 Deploying StockStalker

Backend (FastAPI) + Frontend (Next.js) on **Render**. The database is **Supabase** (already set up — just reuse its connection string).

```
Browser ─► Frontend (Next.js)  ─► Backend (FastAPI)  ─► Supabase (Postgres + pgvector)
          stockstalker-frontend    stockstalker-backend     (external, already created)
```

Order: **Backend → Frontend** (Supabase already exists). Schema (tables + pgvector) is **auto-created on first boot** — no manual DB setup.

---

## Prerequisites
- Repo pushed to GitHub, on the branch you want to deploy.
- A [Render](https://dashboard.render.com) account.
- Your Supabase **Transaction-pooler** connection string (Supabase → Project Settings → Database → Connection string → URI), e.g.
  `postgresql://postgres.<ref>:<pwd>@aws-1-<region>.pooler.supabase.com:6543/postgres`
- A valid **Google AI Studio** Gemini key (`AIza…`, from https://aistudio.google.com/apikey) + a Polygon key.

---

## Step 1 — Backend (Web Service)

New + → **Web Service** → connect repo → branch.

| Field | Value |
|---|---|
| Name | `stockstalker-backend` |
| Root Directory | *(blank — repo root)* |
| Runtime | Python |
| Build Command | `pip install .` |
| Start Command | `uvicorn stockstalker.api.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

**Environment variables:**

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | your AI-Studio key (`AIza…`) |
| `POLYGON_API_KEY` | your Polygon key |
| `DATABASE_URL` | the Supabase pooler URI |
| `FRONTEND_ORIGIN` | `https://stockstalker-frontend.onrender.com` (your frontend URL) |
| `PYTHON_VERSION` | `3.12` |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | *(optional — for the bot + alerts)* |
| `ENABLE_BACKGROUND_JOBS` | *(optional — `true` runs the bot + scheduler in this service; see Telegram section)* |

Create it. After it's **Live**, check `https://stockstalker-backend.onrender.com/health` → `{"status":"ok"}` and `/docs` for Swagger.

---

## Step 2 — Frontend (Web Service)

New + → **Web Service** → same repo + branch.

| Field | Value |
|---|---|
| Name | `stockstalker-frontend` |
| Root Directory | `frontend` |
| Runtime | Node |
| Build Command | `npm install && npm run build` |
| Start Command | `npm start` |

**Environment variables** (all are build-time → set before the build):

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | the backend URL, e.g. `https://stockstalker-backend.onrender.com` |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | from `frontend/.env.local` |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | " |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | " |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | " |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | " |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | " |
| `NODE_VERSION` | `20` |

> `NEXT_PUBLIC_*` are baked in at build time — if you change `NEXT_PUBLIC_API_URL` later, **redeploy** the frontend.

---

## Step 3 — Wire + verify
1. Backend env `FRONTEND_ORIGIN` = the frontend URL (comma-separate for multiple). Save → backend redeploys.
2. Frontend env `NEXT_PUBLIC_API_URL` = the backend URL. (Render URLs are predictable — `https://<name>.onrender.com` — so set both upfront.)
3. Open the frontend → sign up/login (Firebase) → dashboard loads, add a ticker, **Refresh** → analysis appears (writes to Supabase).
4. In Firebase Console → Authentication → Settings → **Authorized domains**, add `stockstalker-frontend.onrender.com`.

---

## Optional — Telegram bot + scheduled jobs
The bot only *answers commands* while a **polling** process runs, and the daily
refresh/summary + alert pushes need the **scheduler** running. Two ways to host them:

### Option A — one service (best for the free plan)
Run the bot + scheduler **inside the backend** — no extra service. On the backend
web service, add one env var:

| Key | Value |
|---|---|
| `ENABLE_BACKGROUND_JOBS` | `true` |

Now the single backend process serves the API **and** polls Telegram **and** runs
the daily jobs. ⚠️ Don't also deploy the worker in Option B — two pollers fight over
one bot token.

> Free Render web services sleep after ~15 min idle, which pauses the bot + scheduler.
> Keep it awake with a **free uptime pinger** (e.g. UptimeRobot or cron-job.org)
> hitting `https://stockstalker-backend.onrender.com/health` every ~10 min. One
> always-on free service fits within Render's ~750 instance-hours/month.

### Option B — separate Background Worker (needs a paid/always-on plan)
New + → **Background Worker**, same repo/branch/root + env vars, with:
- Build: `pip install .`
- Start: `stockstalker run-scheduler`

Leave `ENABLE_BACKGROUND_JOBS` **unset** on the backend in this case. (Render
Background Workers aren't offered on the free plan.)

---

## Environment variables reference

**Backend**

| Key | Req | Notes |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | AI-Studio key (`AIza…`) |
| `POLYGON_API_KEY` | ✅ | |
| `DATABASE_URL` | ✅ | Supabase pooler URI (auto-uses asyncpg) |
| `FRONTEND_ORIGIN` | ✅ | frontend origin(s) for CORS, comma-separated |
| `PYTHON_VERSION` | rec | `3.12` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | – | optional bot + alerts |
| `ENABLE_BACKGROUND_JOBS` | – | `true` = run bot poller + scheduler in the API process (single-service). Don't also run the worker. |

**Frontend**

| Key | Req | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | backend URL (build-time) |
| `NEXT_PUBLIC_FIREBASE_*` (6) | ✅ | from `frontend/.env.local` |
| `NODE_VERSION` | rec | `20` |

---

## Optional — `render.yaml` blueprint
Commit to repo root, then New + → **Blueprint**.

```yaml
services:
  - type: web
    name: stockstalker-backend
    runtime: python
    rootDir: .
    plan: free
    buildCommand: pip install .
    startCommand: uvicorn stockstalker.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - { key: PYTHON_VERSION, value: "3.12" }
      - { key: GEMINI_API_KEY, sync: false }
      - { key: POLYGON_API_KEY, sync: false }
      - { key: DATABASE_URL, sync: false }
      - { key: FRONTEND_ORIGIN, sync: false }

  - type: web
    name: stockstalker-frontend
    runtime: node
    rootDir: frontend
    plan: free
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - { key: NODE_VERSION, value: "20" }
      - { key: NEXT_PUBLIC_API_URL, sync: false }
      - { key: NEXT_PUBLIC_FIREBASE_API_KEY, sync: false }
      - { key: NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN, sync: false }
      - { key: NEXT_PUBLIC_FIREBASE_PROJECT_ID, sync: false }
      - { key: NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET, sync: false }
      - { key: NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID, sync: false }
      - { key: NEXT_PUBLIC_FIREBASE_APP_ID, sync: false }
```

---

## Notes
- **DB schema auto-creates** on first backend boot (`init_db` + pgvector `ensure_schema`); if the pooler role can't `CREATE EXTENSION vector`, enable it once in Supabase → Database → Extensions.
- **Free Render web services sleep** after ~15 min idle (slow cold start). Use Starter for always-on, or — if you run the bot/scheduler in-process (`ENABLE_BACKGROUND_JOBS`) — keep the free service awake with an uptime pinger (see the Telegram section).
- Frontend can alternatively go to **Vercel** (Next.js native): import repo, root `frontend`, add the same `NEXT_PUBLIC_*` vars; then set the backend `FRONTEND_ORIGIN` to the Vercel URL.
