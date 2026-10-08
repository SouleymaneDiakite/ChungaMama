# rag_starter: ChungaMama assistant service

The retrieval-augmented assistant behind ChungaMama's chat. It takes a
conversation, retrieves relevant MOH216 content, classifies intent and risk,
generates a grounded reply in the right language, and tells the backend
whether to escalate.

```
POST /chat   { messages: [{role, content}], session_id }
          →  { intent, entities, risk_level, reply, escalate }
GET  /health
```

## Files

| File | Purpose |
|---|---|
| `rag_core.py` | Shared logic: constants, language detection, prompt building, retrieval, `classify()`, generation |
| `service.py` | FastAPI app exposing `/chat` and `/health`; keeps per-session history |
| `query.py` | Command-line chat over the same core (one-shot or interactive) |
| `ingest.py` | Embeds `moh216_chunks.json` into Postgres (pgvector). **Wipes and rebuilds the table** |
| `ingest_pdf.py` | Ingests a MOH PDF (needs `pypdf`); adds heading/priority metadata |
| `tts.py` | `speak(text, language, output_path)` using gTTS; `python tts.py` writes sample MP3s |
| `moh216_chunks.json` | 18 hand-curated Swahili chunks, each tagged with an intent and source |

## Design

**Plain Python RAG, LangChain only for the vector store.** LangChain's
higher-level chains change a lot between versions and hide behaviour, so
retrieve → prompt → generate is written out in `rag_core.py`. Only
`PGVectorStore` (`langchain-postgres==0.0.17`) is used.

**Models (all swappable constants in `rag_core.py`)**
- Embeddings: `BAAI/bge-m3` (1024-dim) as `EMBEDDING_MODEL`. `VECTOR_SIZE`
  must always match it. Both live only in `rag_core.py`; the ingest scripts
  import them. Changing the embedding model means re-running `ingest.py`.
- Generation: `llama3.1` (8B, ~4.7 GB quantised) via Ollama as `OLLAMA_MODEL`.
  Sized for a 6 GB GPU (RTX 2060).

**Language policy.** `detect_language()` is a word-list heuristic: English
only if English markers appear and no Swahili markers do; mixed input is
answered in Swahili. "Translate to English/Swahili" (and "say that in
English") re-generates from the stored sources rather than translating text.

**Classification (rule-based, replaceable).** `classify()` takes intent from
the top retrieved chunk's tag, risk as the maximum across all retrieved chunks
(`EMERGENCY_SIGNS` → high, `MENTAL_HEALTH_DISTRESS` → medium, others low), a
self-harm keyword override to high, and regex entity extraction (gestational
week/month, symptoms). `escalate = risk_level == "high"`.

**Prompt rules.** Answer only from retrieved sources; never assume symptoms
the user didn't state; never name a diagnosis not in the sources; at high
risk, state clearly that the person should go to a clinic or hospital now.

**Follow-ups.** The previous question is folded into the retrieval query (not
into classification), so vague follow-ups like "it's been 4 hours" still find
the right chunks. Conversation memory is an in-memory dict keyed by
`session_id`.

## Setup

```bash
cd rag_starter
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama pull llama3.1
```

Postgres comes from the project's `docker-compose.yml` (`docker compose up -d`
from the repo root), exposed on host port **5433**.

`.env`:
```
DATABASE_URL=postgresql+psycopg://chungamama:chungamama@localhost:5433/chungamama
```
It must be the psycopg3 form (`postgresql+psycopg://`), unlike the backend's.
An already-set shell `DATABASE_URL` overrides `.env`, so if the service can't
connect, check your shell variable first.

## Run

```bash
python ingest.py                               # load/refresh the knowledge base
python query.py "Nina maumivu makali ya kichwa, nifanye nini?"   # CLI, one-shot
python query.py                                # CLI, interactive
uvicorn service:app --port 9000                # HTTP service for the backend
python tts.py                                  # writes sample_sw.mp3 / sample_en.mp3
```

First `ingest.py` run downloads the embedding model (~2 GB for BGE-M3,
cached afterwards). Confirm Ollama is using the GPU with `ollama ps`.

## Known limitations

- **Unverified GPU performance.** Earlier runs on CPU (llama3.2) were slow
  enough to time out. Re-test `llama3.1` on the GPU before trusting latency.
- **Tiny corpus** (18 chunks). The `sex-during-pregnancy` chunk is flagged
  for verification against the real handbook or a midwife.
- **Session memory is in-process**, unbounded and lost on restart.
- **Rule-based classifier** is a stand-in, not a trained model.
- **Small-model drift:** replies can still add small details not in the
  sources despite the prompt rules.
- **TTS:** gTTS needs internet and has a heavy accent in Swahili.
- **No ASR yet.** Testing in Colab found `Sunbird/SunflowerASR-51-african-languages`
  clearly better than Paza on Swahili (WER about 0.09–0.64 vs 4.4–7.0, with Paza
  looping). It is gated on Hugging Face: accept the terms on the model page and
  use a token. It is not wired into the service.
- `@app.on_event("startup")` is deprecated in newer FastAPI but works.

## Next steps

1. Run the headache/translation transcript on `llama3.1` and confirm GPU speed.
2. Build an evaluation set (retrieval hit rate, risk accuracy).
3. Add and review more source material.
4. Add `transcribe()` (SunflowerASR) and a `POST /chat/audio` endpoint.
5. Replace gTTS with a better Swahili voice.
