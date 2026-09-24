# ChungaMama

Digitizing Kenya's MOH Mother & Child Health Handbook into an interactive,
voice-first assistant. Paper stays the primary record; this is the
intelligent alerting and guidance layer on top of it.

## Architecture

- **backend/** — FastAPI + PostgreSQL (pgvector). Owns auth, patient
  records, and growth/pregnancy data. Proxies conversational requests to
  Mane's standalone ASR/NLU/RAG service rather than embedding it directly —
  see `app/routers/assistant.py` for the API contract.
- **frontend/** — Next.js + Tailwind. Public site (home, guide) + the
  assistant chat UI + a login stub. Dashboard/staff views are the next
  thing to build, role-gated separately from the mother-facing pages.
- **docker-compose.yml** — local Postgres with the pgvector extension
  pre-installed.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for local Postgres) — or point `DATABASE_URL` at any Postgres
  instance with the `vector` extension available.

## Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit if your DB credentials differ
```

Start Postgres (from the repo root):
```bash
docker compose up -d
```

Create the tables (quick local-dev bootstrap — switch to Alembic
migrations once the schema stabilizes):
```bash
python create_tables.py
```

Run the API:
```bash
uvicorn app.main:app --reload --port 8000
```

Check it worked: open http://localhost:8000/docs — should show the
interactive Swagger UI with 6 endpoints (auth register/login, patients
CRUD, assistant chat, health).

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Connecting Mane's assistant service

The backend's `/api/v1/assistant/chat` endpoint proxies to whatever URL is
set as `ASSISTANT_SERVICE_URL` in `backend/.env` (defaults to
`http://localhost:9000/chat`). It expects that service to accept
`{"messages": [...]}` and return
`{"intent", "entities", "risk_level", "reply", "escalate"}` — the contract
already agreed on so his thesis service stays independently deployable and
separately attributable.

Until his service is running, the assistant page will show a connection
error when you try to send a message — that's expected, not a bug in this
scaffold.

## What's stubbed vs. real

**Working end-to-end:** auth register/login (role-gated: mother/chw/clinician/admin), patient CRUD, the assistant proxy route (once Mane's service is up), the escalations pipeline — a high-risk assistant response is automatically persisted with an SBAR-style summary, and the CHW dashboard (`/dashboard`) lists and lets staff mark them reviewed. Access is enforced server-side via JWT + role check, not just hidden in the UI.

**Not yet built:** statistics/analytics view, phone OTP (currently email/password only — Supabase swap is the next real step there), and Alembic migrations (using direct `create_all()` for now, see the schema-change warning below).

## If you already have a running local database

`create_tables.py` uses SQLAlchemy's `create_all()`, which only creates
tables that don't exist yet — it will **not** add new columns to a table
you already created. If you were testing before this update, the `users`
table is now missing the new `full_name` column and any queries touching
it will fail. Easiest fix for local dev (not real data, so safe to wipe):

```bash
# Postgres, from the repo root
docker compose down -v
docker compose up -d
cd backend && python create_tables.py
```

## Adding the hero photo

The homepage expects `frontend/public/hero-photo.jpg`. See
`frontend/public/README_ADD_PHOTO_HERE.txt` for free, properly-licensed
sources (Unsplash/Pexels) — the code gracefully hides the image slot if
the file isn't present yet, so the build won't break without it.

**Security note:** registration currently accepts an optional `role` field for local testing convenience (so you can create a CHW account to see the dashboard). This must be locked down — admin-invite-only, or a separate staff-provisioning flow — before any real deployment. Right now anyone could register themselves as `admin`.

## Suggested next steps

1. Get Mane's service running locally on port 9000 and confirm the full
   chat flow works end to end.
2. Swap email/password-only auth for Supabase (email + phone OTP), per
   the agreed stack.
3. Add the `escalations` table and wire the TODO in
   `assistant.py` to actually persist high-risk cases for CHW review.
4. Build the role-gated dashboard as a separate route group with its own
   auth check.
