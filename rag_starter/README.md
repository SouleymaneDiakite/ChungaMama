# RAG Starter — MOH216 Knowledge Base

A minimal, working retrieval-augmented generation pipeline. This is
deliberately small: 17 content chunks, two scripts, no framework
magic you can't see through. The goal is for you to understand every
step, since you're new to this and will need to extend it yourself.

## What's here

- `moh216_chunks.json` — 17 chunks of MOH216 content (danger signs,
  nutrition, immunization, birth plan, father's support, mental
  health), each tagged with the intent category it maps to and the
  handbook page it came from
- `ingest.py` — embeds each chunk and stores it in Postgres (pgvector)
- `query.py` — the actual RAG loop: retrieve relevant chunks →
  build a grounded prompt → generate an answer

## Why plain Python instead of a LangChain "chain"

LangChain's chain APIs (`RetrievalQA` and similar) have changed
significantly across recent versions — code you find in tutorials
often won't run on the current version. `query.py` uses LangChain
only for the vector store (`PGVectorStore`), which is stable, and
writes the retrieve → prompt → generate steps as plain Python. Open
`query.py` and read it top to bottom — that's the whole RAG algorithm,
in about 20 lines you can actually follow.

## Setup

```bash
cd rag_starter
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt langchain-huggingface
cp .env.example .env           # fill in your DATABASE_URL and ANTHROPIC_API_KEY
```

Uses the same Postgres container from ChungaMama's `docker-compose.yml`
— make sure it's running (`docker compose up -d` from the project root).

## Run it

```bash
python ingest.py
```
First run downloads the embedding model (~470MB, one-time, cached
after). This embeds all 17 chunks and stores them.

```bash
python query.py "Nina maumivu makali ya kichwa, nifanye nini?"
```
You'll see which chunks got retrieved (with their source page) and
then a generated answer grounded in only those chunks.

## What I verified vs. what needs your machine

I tested the chunk data, the retrieval logic (using a simple
keyword-overlap stand-in — a real headache question correctly surfaced
the danger-signs chunks first), and that every package installs and
imports cleanly. What I *couldn't* test here: downloading the actual
embedding model weights and running against a live Postgres — this
sandbox can't reach huggingface.co or run a persistent database. Both
should just work on your machine; if `ingest.py` fails, the error
message will tell you which of those two steps it's stuck on.

## Next steps, in order

1. **Run it as-is** to see the full loop working end to end.
2. **Expand the corpus.** 17 chunks is a proof of concept, not a real
   knowledge base. Extract the rest of MOH216's narrative sections
   (not the blank clinical forms) the same way, or write a PDF-parsing
   script if you want it automated rather than hand-curated.
3. **Swap the model in `query.py`** for whatever Mane's actual pipeline
   ends up using — right now it calls Claude directly as a stand-in,
   the same way the earlier Wizard-of-Oz prototype did.
4. **Wire this into the real assistant service** — right now
   `ChungaMama/backend`'s `assistant.py` router calls out to
   `ASSISTANT_SERVICE_URL`, expecting a service that returns
   `{intent, entities, risk_level, reply, escalate}`. This RAG loop is
   the "reply" part of that — it still needs the NLU layer (intent
   classification, entity extraction) in front of it, and the
   dialogue-manager / risk-scoring logic around it, per the system
   design document.
