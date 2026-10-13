"""
Loads moh216_chunks.json, embeds each chunk with a free multilingual
model (runs locally, no API cost), and stores them in Postgres via
pgvector so they can be searched later.

Run once to set up, and again any time moh216_chunks.json changes.

Usage:
    python ingest.py            # add/replace the MOH216 chunks; leaves PDFs and
                                # anything else in the table untouched
    python ingest.py --reset    # DROP the whole table first (this deletes PDF
                                # chunks too). Needed after changing the
                                # embedding model, because old vectors have
                                # the wrong size/meaning.
"""
import argparse
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

from rag_core import DATABASE_URL, EMBEDDING_MODEL, TABLE_NAME, VECTOR_SIZE, stable_id

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="drop the whole table first (also deletes PDF chunks)")
    args = parser.parse_args()

    with open("moh216_chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from moh216_chunks.json")

    print(f"Loading embedding model ({EMBEDDING_MODEL})... this downloads once, then caches.")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    engine = PGEngine.from_connection_string(url=DATABASE_URL)

    # Earlier versions dropped and recreated the table on EVERY run, which
    # silently deleted anything ingest_pdf.py had stored. Now the table is
    # only dropped with --reset; otherwise an existing table is kept and just
    # this file's chunks are replaced (by stable id, below).
    try:
        engine.init_vectorstore_table(
            table_name=TABLE_NAME,
            vector_size=VECTOR_SIZE,
            overwrite_existing=args.reset,
        )
    except Exception as e:
        if "already exists" in str(e).lower() and not args.reset:
            print(f"Table '{TABLE_NAME}' exists: keeping it (use --reset to rebuild from scratch).")
        else:
            raise

    store = PGVectorStore.create_sync(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embeddings,
    )

    ids = [stable_id(f"moh216:{chunk['id']}") for chunk in chunks]
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

    # Replace, don't duplicate: remove any earlier copy of these exact chunks.
    store.delete(ids=ids)
    store.add_documents(documents, ids=ids)
    print(f"Stored {len(documents)} chunks in the '{TABLE_NAME}' table.")


if __name__ == "__main__":
    main()
