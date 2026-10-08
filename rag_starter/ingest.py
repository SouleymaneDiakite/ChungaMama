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

from rag_core import DATABASE_URL, EMBEDDING_MODEL, TABLE_NAME, VECTOR_SIZE

load_dotenv()

# EMBEDDING_MODEL and VECTOR_SIZE come from rag_core.py on purpose — that's
# the ONLY place they're defined, so ingest.py (which builds the vectors)
# and query.py/service.py (which search them) can never drift out of sync.
# BAAI/bge-m3 is a retrieval-tuned multilingual model (1024-dim), not just
# a general sentence-similarity one — it replaced the old MiniLM model
# because retrieval was consistently failing to surface the correct
# EMERGENCY_SIGNS chunk across real test queries. It's a bigger download
# (~2.2GB, one-time) and slower per-embedding than MiniLM, but runs fine
# on CPU for a dataset this small (17 chunks).


def main():
    with open("moh216_chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from moh216_chunks.json")

    print(f"Loading embedding model ({EMBEDDING_MODEL})... this downloads once, then caches.")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    engine = PGEngine.from_connection_string(url=DATABASE_URL)

    # NOTE: this is NOT safe to call blindly if the table already exists —
    # init_vectorstore_table does a plain CREATE TABLE under the hood, so a
    # second run against an existing table raises DuplicateTableError
    # rather than confirming the schema (an earlier version of this
    # comment claimed otherwise; that was wrong). overwrite_existing=True
    # drops and recreates it, which is exactly what you want here: you're
    # switching embedding models (384-dim MiniLM -> 1024-dim bge-m3), so
    # any rows from the old table are the wrong dimension anyway and
    # cannot be reused regardless.
    engine.init_vectorstore_table(
        table_name=TABLE_NAME,
        vector_size=VECTOR_SIZE,
        overwrite_existing=True,
    )

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
