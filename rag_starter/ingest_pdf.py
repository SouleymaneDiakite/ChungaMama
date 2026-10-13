"""
Generic PDF ingestion — chunks any PDF and loads it into the same
vector store ingest.py uses, tagged with its own source name so it
never gets confused with MOH216/WHO content downstream.

Usage:
    python ingest_pdf.py path/to/document.pdf "WHO Guidelines" --priority high
    python ingest_pdf.py path/to/encyclopedia.pdf "General Medical Encyclopedia" --priority low
"""
import argparse
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

from rag_core import DATABASE_URL, EMBEDDING_MODEL, TABLE_NAME, stable_id

load_dotenv()

# DATABASE_URL/EMBEDDING_MODEL/TABLE_NAME come from rag_core.py — same
# reason as in ingest.py: this script embeds into the SAME table ingest.py
# creates, so it must use the exact same embedding model (now BAAI/bge-m3)
# or similarity search across the combined table silently breaks (mixed
# dimensions/spaces, no error, just wrong results).

# How much text per chunk, and how much consecutive chunks overlap —
# overlap means a sentence split across a chunk boundary still appears
# whole in at least one chunk, so nothing gets lost mid-thought.
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("source_name", help='Human-readable source name, e.g. "WHO Guidelines"')
    parser.add_argument(
        "--priority", choices=["high", "medium", "low"], default="medium",
        help="high = authoritative maternal-health source (WHO, MOH216); "
             "low = general reference (e.g. a broad medical encyclopedia)",
    )
    args = parser.parse_args()

    print(f"Reading {args.pdf_path}...")
    reader = PdfReader(args.pdf_path)
    print(f"{len(reader.pages)} pages found. Extracting and chunking...")

    documents = []
    ids = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue  # skip blank/image-only pages
        for chunk_num, chunk in enumerate(chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)):
            # Stable id: re-ingesting the same PDF under the same name
            # replaces its chunks instead of piling up duplicates.
            ids.append(stable_id(f"pdf:{args.source_name}:{page_num}:{chunk_num}"))
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": args.source_name,
                        # query.py prints/prompts with metadata['heading'] for
                        # every retrieved chunk regardless of origin — PDF
                        # chunks have no hand-written heading like the MOH216
                        # ones do, so this is a stand-in that keeps that
                        # lookup from KeyError-ing the moment a PDF chunk
                        # gets retrieved.
                        "heading": f"{args.source_name}, page {page_num}",
                        "page": page_num,
                        "priority": args.priority,
                    },
                )
            )

    print(f"Built {len(documents)} chunks from {len(reader.pages)} pages.")
    if not documents:
        print("Nothing to store — is this a scanned/image-only PDF? Those need OCR first.")
        return

    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    engine = PGEngine.from_connection_string(url=DATABASE_URL)
    store = PGVectorStore.create_sync(
        engine=engine, table_name=TABLE_NAME, embedding_service=embeddings,
    )

    # Large PDFs: add in batches so one failure doesn't lose everything,
    # and so you get progress feedback rather than a long silent wait.
    store.delete(ids=ids)
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        store.add_documents(batch, ids=ids[i:i + batch_size])
        print(f"  Stored {min(i + batch_size, len(documents))}/{len(documents)} chunks...")

    print(f"Done. '{args.source_name}' is now searchable alongside MOH216.")


if __name__ == "__main__":
    main()
