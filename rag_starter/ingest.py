"""
Loads moh216_chunks.json, embeds each chunk with a free multilingual
model (runs locally, no API cost), and stores them in Postgres via
pgvector so they can be searched later.

Run once to set up, and again any time moh216_chunks.json changes.

Usage:
    python ingest.py
"""
import asyncio
import json
import os
import sys

# Windows-specific fix: psycopg's async mode (used internally by
# langchain-postgres) is incompatible with Windows' default
# ProactorEventLoop. This must run before any other code creates an
# event loop, so it's the very first thing after the imports it needs.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
TABLE_NAME = "moh216_chunks"

# paraphrase-multilingual-MiniLM-L12-v2: supports 50+ languages including
# Swahili, runs on CPU, ~470MB download (one-time, cached locally after).
# Free — no API key, no per-call cost, since this runs entirely on your
# own machine rather than calling a hosted embedding API.
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE = 384  # must match the embedding model's output dimension


def main():
    with open("moh216_chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from moh216_chunks.json")

    print(f"Loading embedding model ({EMBEDDING_MODEL})... this downloads once, then caches.")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    engine = PGEngine.from_connection_string(url=DATABASE_URL)

    # Safe to call even if the table already exists from a previous run —
    # it won't duplicate or error, just confirms the schema.
    engine.init_vectorstore_table(table_name=TABLE_NAME, vector_size=VECTOR_SIZE)

    store = PGVectorStore.create_sync(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embeddings,
    )

    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "id": chunk["id"],
                "topic": chunk["topic"],
                "intent": chunk["intent"],
                "heading": chunk["heading"],
                "source": chunk["source"],
            },
        )
        for chunk in chunks
    ]

    store.add_documents(documents)
    print(f"Stored {len(documents)} chunks in the '{TABLE_NAME}' table.")


if __name__ == "__main__":
    main()
