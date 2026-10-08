"""
Shared RAG logic used by BOTH query.py (CLI, for your own testing) and
service.py (the HTTP service that backend/app/routers/assistant.py
actually calls in production).

This file is the seam described in the project plan: retrieval, language
handling, classification, and generation all live here ONCE. query.py and
service.py are thin front ends over the same functions, so nothing behind
this file needs to change if you later swap the embedding model, add a
real ML classifier, or point OLLAMA_MODEL at a fine-tuned checkpoint.

Written in plain Python, not a LangChain "chain" — see README for why.
"""
import asyncio
import os
import re
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

# BAAI/bge-m3: a retrieval-tuned multilingual embedding model (not just a
# general sentence-similarity model like the old MiniLM). On MIRACL's
# Swahili benchmark it scores 78.6 nDCG@10 (dense) vs multilingual-e5-large's
# 74.9 — a real, Swahili-specific, published gap, not a reputation claim.
# This MUST match the model used in ingest.py, and VECTOR_SIZE must match
# this model's output dimension (1024 for bge-m3, vs 384 for the old
# MiniLM model) — changing either one without the other breaks retrieval
# silently (cosine similarity on mismatched dimensions doesn't error, it
# just returns garbage), so treat these two constants as a pair.
EMBEDDING_MODEL = "BAAI/bge-m3"
VECTOR_SIZE = 1024

OLLAMA_MODEL = "llama3.2"  # swap to "llama3.1" (or a fine-tuned GGUF model
                           # name via a Modelfile) once you have the GPU —
                           # this is the ONE line that changes for that.

TOP_K = 3  # how many chunks to retrieve per question

# --- language detection ---------------------------------------------------
# Deliberately a transparent word-list heuristic, not a model call or an
# external library — all it actually has to decide is "overwhelmingly
# English" vs "everything else", since pure-Swahili AND mixed/code-switched
# text get the SAME treatment (respond in Swahili) under the project's
# language policy.

ENGLISH_MARKERS = {
    "the", "is", "are", "was", "were", "what", "when", "where", "why", "how",
    "and", "or", "but", "with", "for", "from", "this", "that", "these",
    "my", "your", "i", "you", "he", "she", "it", "we", "they", "am",
    "can", "should", "would", "will", "do", "does", "did", "have", "has",
    "pain", "hurt", "hurts", "hurting", "feel", "feeling", "pregnant",
    "pregnancy", "baby", "doctor", "clinic", "hospital", "sick", "help",
    "please", "since", "morning", "yesterday", "today", "week", "weeks",
    "month", "months",
}

SWAHILI_MARKERS = {
    "na", "ya", "wa", "ni", "kwa", "hii", "huu", "hiyo", "yangu", "wangu",
    "nina", "ninaumwa", "naumwa", "nafaa", "nianze", "nifanye", "nini",
    "lini", "wapi", "vipi", "mimba", "mtoto", "watoto", "maumivu", "makali",
    "daktari", "kliniki", "hospitali", "mgonjwa", "msaada", "tafadhali",
    "mimi", "wewe", "yeye", "sisi", "wao", "leo", "jana", "asubuhi",
    "miezi", "wiki", "siku", "kichwa", "tumbo", "miguu", "damu", "homa",
}

# Direction-specific phrases checked first, so "translate that to swahili"
# doesn't get mistaken for a request to translate TO English.
TO_ENGLISH_CUES = (
    "to english", "in english", "kwa kiingereza", "english please",
    "in inglish",
)
TO_SWAHILI_CUES = (
    "to swahili", "in swahili", "kwa kiswahili", "swahili please",
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def detect_language(text: str) -> str:
    """Returns 'en' only when the text is overwhelmingly/purely English.
    Pure Swahili and mixed/code-switched text both return 'sw' — that's
    the policy: mixed input defaults to Swahili."""
    tokens = _tokenize(text)
    if not tokens:
        return "sw"

    en_hits = sum(1 for t in tokens if t in ENGLISH_MARKERS)
    sw_hits = sum(1 for t in tokens if t in SWAHILI_MARKERS)

    if en_hits > 0 and sw_hits == 0:
        return "en"
    return "sw"


def requested_translation_language(text: str, last_language: str | None) -> str | None:
    """Returns 'en' or 'sw' if this looks like a translation request, with
    which language it's asking FOR. Returns None otherwise. A bare
    "translate that" with no stated direction falls back to the opposite
    of the previous answer's language."""
    lowered = text.lower()

    if any(cue in lowered for cue in TO_ENGLISH_CUES):
        return "en"
    if any(cue in lowered for cue in TO_SWAHILI_CUES):
        return "sw"
    if "translate" in lowered and last_language:
        return "en" if last_language == "sw" else "sw"
    return None


# --- retrieval --------------------------------------------------------------

def get_store():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    engine = PGEngine.from_connection_string(url=DATABASE_URL)
    return PGVectorStore.create_sync(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embeddings,
    )


def build_system_prompt(context: str, target_language: str, risk_level: str = "low") -> str:
    if target_language == "en":
        language_instruction = "Respond in English."
        closing_reminder = (
            "\n\nIMPORTANT: Write your entire answer in English, even "
            "though the sources above are written in Swahili."
        )
    else:
        language_instruction = "Respond in Swahili."
        closing_reminder = "\n\nIMPORTANT: Write your entire answer in Swahili."

    # When classify() has flagged this as high risk, don't let the model
    # fall back on a generic "consult a provider" non-answer when the
    # sources actually name the danger signs — that was a real observed
    # failure (a headache question retrieved the correct emergency-signs
    # chunk, but the model ignored it and gave a content-free deflection).
    # A vague deflection is worse than useless here: it wastes the one
    # moment the knowledge base actually had the right warning to give.
    if risk_level == "high":
        urgency_instruction = (
            " This question may describe a pregnancy/postpartum danger "
            "sign. If the sources list danger signs relevant to the "
            "question, name them explicitly and tell the user to seek "
            "care at a clinic or hospital immediately — do not only say "
            "'consult a healthcare provider' without stating why or what "
            "to watch for."
        )
    else:
        urgency_instruction = ""

    # Added after a real observed failure: the model was attributing
    # symptoms the user never mentioned (e.g. "vaginal bleeding") to them,
    # just because the retrieved danger-signs chunk lists bleeding
    # alongside other signs — and, worse, inventing a specific diagnosis
    # ("placenta abruption") that appears NOWHERE in the knowledge base at
    # all. "Answer using only the sources" was not strong enough on its
    # own to stop this; it needed to be told explicitly not to assume the
    # user has a symptom they didn't state, and not to name any diagnosis
    # unless it's literally present in the sources.
    grounding_instruction = (
        " Only treat a symptom as something the user is experiencing if "
        "they actually said so in their question — do not assume they "
        "have a symptom just because it's listed in the sources alongside "
        "others. When listing danger signs from the sources, present them "
        "as things to watch for in general, not as things the user has "
        "reported. Never name a specific medical diagnosis (e.g. a named "
        "condition or complication) unless that exact diagnosis appears in "
        "the sources below — if the sources only list symptoms, stick to "
        "symptoms and do not guess at an underlying cause."
    )

    return (
        "You are a Swahili/English maternal health assistant. Answer the "
        "question using ONLY the information in the provided sources below. "
        "If the sources don't contain enough information to answer "
        "confidently, say so rather than guessing. "
        f"{language_instruction} Keep the answer short and simple, suitable "
        f"for someone with limited reading ability.{grounding_instruction}"
        f"{urgency_instruction}\n\n"
        f"SOURCES:\n{context}"
        f"{closing_reminder}"
    )


def generate_stream(system_prompt: str, user_question: str):
    """For the CLI: yields text chunks as they arrive, so query.py can
    print tokens live. stream=True is what distinguishes "slow / cold
    model load" from "actually hung" — see query.py for why that matters."""
    stream = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]


def generate_text(system_prompt: str, user_question: str) -> str:
    """For the API: blocks and returns the full answer as one string —
    an HTTP JSON response can't be half-streamed the way a terminal can,
    and the backend's assistant.py proxy expects one `reply` field."""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        stream=False,
    )
    return response["message"]["content"]


# --- classification (intent / entities / risk_level / escalate) ------------
# Rule-based on purpose, not a placeholder to feel embarrassed about: it
# reuses the intent/priority tags you already hand-curated in
# moh216_chunks.json, so it's as accurate as your source data and fully
# explainable in a defense ("the top retrieved chunk is tagged
# EMERGENCY_SIGNS, so risk_level is high") rather than a black box. This
# function is the seam — swap its body for a trained classifier later and
# nothing outside this function has to change, because the shape of what
# it returns (the {intent, entities, risk_level, escalate} contract) stays
# the same either way.

# Any single one of these, anywhere in the question, overrides whatever
# the retrieved chunks suggest — a disclosure of self-harm risk is an
# escalation regardless of what topic the retrieval system thinks this is.
SELF_HARM_MARKERS = (
    "kujiua", "kujidhuru", "nimechoka kuishi", "sitaki kuishi",
    "suicide", "kill myself", "end my life", "hurt myself",
    "harm myself", "don't want to live", "do not want to live",
)

# Maps a chunk's `intent` tag (from moh216_chunks.json) to a risk level.
# EMERGENCY_SIGNS and MENTAL_HEALTH_DISTRESS are the two categories in the
# current dataset where silence or a wrong answer is actually dangerous;
# everything else is informational.
INTENT_RISK_MAP = {
    "EMERGENCY_SIGNS": "high",
    "MENTAL_HEALTH_DISTRESS": "medium",
    "BIRTH_PLAN": "low",
    "GENERAL_PRENATAL": "low",
    "NUTRITION": "low",
    "VACCINATION_SCHED": "low",
}

# Very small, deliberately named entity extractors — not a general NER
# model, just the handful of fields that matter for a maternal-health
# assistant and that a regex can reliably catch: how far along the
# pregnancy is, and which symptoms were actually mentioned.
_WEEK_RE = re.compile(r"\b(?:wiki|week|weeks)\s*(\d{1,2})\b", re.IGNORECASE)
_MONTH_RE = re.compile(r"\b(?:miezi|mwezi|month|months)\s*(\d{1,2})\b", re.IGNORECASE)

SYMPTOM_KEYWORDS = {
    "kichwa": "headache", "headache": "headache",
    "damu": "bleeding", "bleeding": "bleeding",
    "homa": "fever", "fever": "fever",
    "tumbo": "abdominal_pain", "abdominal": "abdominal_pain",
    "miguu": "leg_pain", "leg": "leg_pain",
    "kifafa": "convulsions", "convulsions": "convulsions", "seizure": "convulsions",
    "uvimbe": "swelling", "swelling": "swelling",
    "msogeo": "reduced_fetal_movement", "movement": "reduced_fetal_movement",
}


def extract_entities(text: str) -> dict:
    lowered = text.lower()
    entities: dict = {}

    week_match = _WEEK_RE.search(lowered)
    if week_match:
        entities["gestational_week"] = int(week_match.group(1))

    month_match = _MONTH_RE.search(lowered)
    if month_match:
        entities["gestational_month"] = int(month_match.group(1))

    symptoms = sorted({
        label for keyword, label in SYMPTOM_KEYWORDS.items() if keyword in lowered
    })
    if symptoms:
        entities["symptoms"] = symptoms

    return entities


_RISK_RANK = {"low": 0, "medium": 1, "high": 2}


def classify(question: str, retrieved_docs: list) -> dict:
    """retrieved_docs is the list of langchain Documents returned by
    similarity_search — same objects used to build the prompt context.

    risk_level is the HIGHEST risk among ALL retrieved docs, not just the
    top-ranked one. Using only doc #1 was a real bug: a "terrible headache"
    question correctly retrieved the EMERGENCY_SIGNS chunk (severe headache
    is a listed pregnancy danger sign) but ranked it 3rd behind a mental-
    health chunk, so risk_level came back "medium" instead of "high". A
    safety classifier should err toward whichever retrieved source is most
    concerning, not whichever one the embedding model liked best."""
    entities = extract_entities(question)

    top_intent = retrieved_docs[0].metadata.get("intent") if retrieved_docs else None

    risk_level = "low"
    for doc in retrieved_docs:
        doc_risk = INTENT_RISK_MAP.get(doc.metadata.get("intent"), "low")
        if _RISK_RANK[doc_risk] > _RISK_RANK[risk_level]:
            risk_level = doc_risk
    escalate = risk_level == "high"

    lowered = question.lower()
    if any(marker in lowered for marker in SELF_HARM_MARKERS):
        risk_level = "high"
        escalate = True
        top_intent = top_intent or "MENTAL_HEALTH_DISTRESS"

    return {
        "intent": top_intent or "UNKNOWN",
        "entities": entities,
        "risk_level": risk_level,
        "escalate": escalate,
    }


# --- the shared retrieval+classification step -------------------------------

def retrieve(store, question: str, prior_question: str | None = None) -> dict:
    """Runs retrieval and classification only — no generation. Returns
    everything both query.py and service.py need to then call
    generate_stream/generate_text with the right prompt.

    prior_question, when given, is folded into the SEARCH query (not into
    classification/entities — those stay scoped to the current message).
    This matters for a real observed gap: a vague follow-up like "it has
    been 4 hours, do I still need to go to hospital?" shares no words with
    "terrible headache", so on its own it can retrieve something unrelated
    and silently let risk_level drop back to low on what is still the same
    danger-sign conversation. Searching on both questions together keeps
    the original symptom in view for the follow-up."""
    search_query = f"{prior_question} {question}" if prior_question else question
    results = store.similarity_search(search_query, k=TOP_K)

    context = "\n\n".join(
        f"Source: {doc.metadata['source']} — {doc.metadata['heading']}\n{doc.page_content}"
        for doc in results
    )

    classification = classify(question, results)

    return {
        "results": results,
        "context": context,
        "classification": classification,
    }
