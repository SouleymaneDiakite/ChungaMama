# ChungaMama

A bilingual (Swahili/English) maternal-health assistant built on Kenya's MOH
Mother & Child Health Handbook (MOH216). Paper stays the primary record; this
is the guidance and escalation layer on top of it.

> **Prototype.** Not a substitute for medical care. Answers come from a small,
> partly unverified knowledge base (see [Known limitations](#known-limitations)).

## Architecture

```
Browser (Next.js :3000)
   │  POST /api/v1/assistant/chat   { messages, session_id }
   ▼
Backend (FastAPI :8000)  ── auth, patients, escalations (Postgres)
   │  POST ASSISTANT_SERVICE_URL    { messages, session_id }
   ▼
Assistant service (rag_starter/service.py, FastAPI :9000)
   │  retrieve (pgvector) → classify → generate (Ollama)
   ▼
{ intent, entities, risk_level, reply, escalate }
```

- **frontend/**: Next.js + Tailwind. Public site, handbook guide, assistant
  chat, login/register, and a role-gated staff dashboard (`/dashboard`).
  Swahili/English toggle via `lib/i18n.tsx`. Each browser tab gets its own
  `session_id`, so conversations don't mix.
- **backend/**: FastAPI + SQLAlchemy + Postgres. Owns auth (JWT, roles:
  mother/chw/clinician/admin), patient records and escalations. The assistant
  route is a thin proxy; when the service returns `escalate: true`, the
  backend saves an `Escalation` row for CHW review.
- **rag_starter/**: the assistant service (retrieval, rule-based
  classification, local LLM, TTS). See [rag_starter/README.md](rag_starter/README.md).
- **docker-compose.yml**: Postgres with pgvector, exposed on host port **5433**.

The HTTP contract between backend and assistant service is the only coupling,
so the retrieval, model, classifier or voice components can be swapped without
touching the backend or frontend.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (or any Postgres with the `vector` extension)
- [Ollama](https://ollama.com) for local generation (the assistant service)
- An NVIDIA GPU is strongly recommended for the assistant (see the
  rag_starter README); CPU works but replies can take minutes.

## Running everything locally

You need four things running. Use separate terminals.

**1. Postgres**
```bash
docker compose up -d
```

**2. Assistant service** (full setup in `rag_starter/README.md`)
```bash
cd rag_starter
python -m venv venv && venv\Scripts\activate     # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.1
cp .env.example .env
python ingest.py            # once, loads the knowledge base
uvicorn service:app --port 9000
```

**3. Backend**
```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then edit, see below
python create_tables.py     # once
uvicorn app.main:app --reload --port 8000
```

**4. Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. API docs: http://localhost:8000/docs (backend) and
http://localhost:9000/docs (assistant service). `GET :9000/health` should
return 200.

### Environment

`.env` files are git-ignored. Never commit them.

| File | Variable | Notes |
|---|---|---|
| `backend/.env` | `DATABASE_URL` | `postgresql://chungamama:chungamama@localhost:5433/chungamama` (note port 5433) |
| `backend/.env` | `SECRET_KEY` | Replace the placeholder |
| `backend/.env` | `ASSISTANT_SERVICE_URL` | `http://127.0.0.1:9000/chat` (`127.0.0.1` avoids `localhost` resolving oddly on Windows) |
| `rag_starter/.env` | `DATABASE_URL` | psycopg3 form: `postgresql+psycopg://chungamama:chungamama@localhost:5433/chungamama` |
| frontend (optional) | `NEXT_PUBLIC_API_URL` | Defaults to `http://localhost:8000/api/v1/assistant/chat` |

**Gotcha:** an already-set shell `DATABASE_URL` takes precedence over `.env`
(python-dotenv doesn't override it), and `uvicorn --reload` doesn't watch
`.env`. If the service can't reach the database, check
`echo $env:DATABASE_URL` (PowerShell) / `echo $DATABASE_URL` first, then
restart the server.

## Status

**Working end to end**
- Register/login with role-based access enforced server-side (JWT)
- Patient CRUD
- Chat → backend → assistant service → grounded reply, in Swahili or English
- Risk handling: high-risk replies are saved as escalations with an
  SBAR-style summary; staff review them on `/dashboard`
- Friendly bilingual fallback in the UI when the assistant is unreachable
  (it also tells users to go to a clinic if urgent)

**Not built yet**
- Voice input (ASR) and voice output in the UI. The ASR model has been
  chosen (SunflowerASR) but is not wired in. `rag_starter/tts.py` exists but
  has no endpoint yet.
- Statistics/analytics view
- Phone OTP login (email/password only)
- Alembic migrations (`create_all()` for now)
- Persistent chat memory (see limitations)
- Automated retrieval/risk evaluation set

## Known limitations

- **Knowledge base is small** (18 Swahili chunks). The
  `sex-during-pregnancy` chunk is flagged in its `source` field as needing
  verification against the real MOH216 text or a midwife.
- **Classifier is rule-based**: intent comes from the top retrieved chunk's
  tag, risk is the highest across retrieved chunks, plus a self-harm keyword
  override. It is a stand-in that can be replaced behind the same contract.
- **Session memory is in-process** (`service.py`): it resets on restart and
  grows without bound. Fine for a prototype, not for deployment.
- **Generation speed is unverified on GPU.** The backend timeout is 180s
  (a CPU-era workaround in `assistant.py`); lower it once GPU latency is
  confirmed.
- **TTS (gTTS)** needs internet and has a noticeable accent in Swahili.
- Small local models can still drift from the retrieved sources. The prompt
  restricts them, but this is not eliminated.

## Security notes

- Registration accepts an optional `role` for local testing, so anyone can
  register as `admin`. Lock this down (invite-only or staff provisioning)
  before any real deployment.
- Replace `SECRET_KEY` and the default database credentials outside local dev.

## If you already have a local database

`create_tables.py` uses `create_all()`, which creates missing tables but does
not add columns to existing ones. After schema changes, wipe the local dev DB:

```bash
docker compose down -v
docker compose up -d
cd backend && python create_tables.py
```

## Hero photo

The homepage looks for `frontend/public/hero-photo.jpg`. See
`frontend/public/README_ADD_PHOTO_HERE.txt` for licensed sources. The build
works without it.

## Next steps

1. Confirm GPU generation speed, then lower the backend timeout.
2. Evaluation set and script (retrieval hit rate, risk accuracy).
3. Add and verify more knowledge-base content.
4. Wire in `transcribe()` (SunflowerASR), an audio endpoint, and mic/play
   buttons in the UI.
5. Better Swahili TTS; phone OTP; migrations; lock down registration roles.
