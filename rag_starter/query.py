"""
The actual RAG loop, written in plain Python rather than a LangChain
"chain" — see README for why.

Uses Ollama for generation — a free, local model, no API key needed.
Requires Ollama installed and running (ollama.com), with a model
pulled: `ollama pull llama3.2`.

Usage:
    python query.py "Nina maumivu makali ya kichwa, nifanye nini?"
"""
import asyncio
import os
import sys

# Windows-specific fix — see ingest.py for why this is needed.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
import ollama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
TABLE_NAME = "moh216_chunks"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL = "llama3.2"  # swap for "llama3.1" if you have 8GB+ RAM free

TOP_K = 3  # how many chunks to retrieve per question


def get_store():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    engine = PGEngine.from_connection_string(url=DATABASE_URL)
    return PGVectorStore.create_sync(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embeddings,
    )


def answer_question(question: str) -> None:
    store = get_store()

    # Step 1: retrieve. Identical regardless of which model does
    # generation — this part doesn't touch Claude, Ollama, or anything
    # else, it's pure vector search against your own database.
    results = store.similarity_search(question, k=TOP_K)

    if not results:
        print("No relevant guidance found in the knowledge base.")
        return

    print("--- Retrieved sources ---")
    for doc in results:
        print(f"  [{doc.metadata['source']}] {doc.metadata['heading']}")
    print()

    # Step 2: build a prompt that includes only the retrieved content.
    context = "\n\n".join(
        f"Source: {doc.metadata['source']} — {doc.metadata['heading']}\n{doc.page_content}"
        for doc in results
    )

    system_prompt = (
        "You are a Swahili maternal health assistant. Answer the question "
        "using ONLY the information in the provided sources below. If the "
        "sources don't contain enough information to answer confidently, "
        "say so rather than guessing. Respond in the same language as the "
        "question. Keep the answer short and simple, suitable for someone "
        "with limited reading ability.\n\n"
        f"SOURCES:\n{context}"
    )

    # Step 3: generate, using a free local model via Ollama — no API
    # key, no per-call cost, runs entirely on this machine.
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    print("--- Answer ---")
    print(response["message"]["content"])


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Ni dalili gani za hatari wakati wa ujauzito?"
    answer_question(q)
