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
import uuid
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

OLLAMA_MODEL = "llama3.1"  # Now that the GPU is in hand: llama3.1 (8B) over
                           # llama3.2 (3B). A Q4 quant of the 8B model is
                           # ~4.7GB, fits comfortably in 6GB VRAM. This was
                           # the ONE line that needed to change for that —
                           # everything else (prompt, retrieval, classify())
                           # stays exactly the same. If it's still slow after
                           # this, confirm Ollama is actually using the GPU
                           # (`ollama ps` should show a GPU name/percentage,
                           # not "100% CPU") rather than assuming the model
                           # swap alone fixes it.

TOP_K = 3  # how many chunks go into the prompt per question
# How many candidates to fetch. Risk is judged from the CURATED (intent-tagged)
# chunks among these candidates, not only the top TOP_K, so a pile of PDF
# chunks (which have no intent) can't push the danger-sign chunk out of view
# and quietly make a dangerous question look low-risk.
CANDIDATE_K = 15
# Curated chunks farther than this are ignored for risk (unrelated question).
RISK_MAX_DISTANCE = 0.5

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
    # Added so short, valid English replies ("Seek care immediately.") are
    # recognised as English when we validate a translation. None of these
    # are Swahili words.
    "to", "a", "an", "of", "in", "on", "at", "if", "not", "be", "go",
    "seek", "care", "immediately", "right", "away", "as", "because",
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
    "to english", "in english", "into english", "kwa kiingereza",
    "english please", "in inglish", "to en", "in en", "into en",
)
TO_SWAHILI_CUES = (
    "to swahili", "in swahili", "into swahili", "kwa kiswahili",
    "swahili please", "to sw", "in sw", "into sw",
)
# Bare verbs that mean "translate", used when no direction is given.
TRANSLATE_WORDS = ("translate", "tafsiri")

# Shown when someone asks to translate but there is no earlier answer in
# this session to translate (fresh session, one-shot CLI run, or the
# service restarted). Returned INSTEAD of falling through to retrieval:
# searching the knowledge base for the text "translate to en" returns
# unrelated chunks, and the model then invents an answer from them.
NOTHING_TO_TRANSLATE = {
    "sw": "Bado sina jibu la kutafsiri. Uliza swali lako kwanza, kisha niombe nitafsiri.",
    "en": "I don't have an answer to translate yet. Ask your question first, then ask me to translate it.",
}


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
    # Match cues on word boundaries so "to en" doesn't fire inside
    # "to enter" / "to ensure", and "in sw" doesn't fire inside "in swollen".
    def has(cue: str) -> bool:
        return re.search(rf"(?<![a-z]){re.escape(cue)}(?![a-z])", lowered) is not None

    if any(has(c) for c in TO_ENGLISH_CUES):
        return "en"
    if any(has(c) for c in TO_SWAHILI_CUES):
        return "sw"
    if any(w in lowered for w in TRANSLATE_WORDS):
        # A language name wins over flipping, so typos in the rest of the
        # sentence ("translate rto english", "translate to kiswahili") work.
        names_en = has("english") or has("inglish") or has("kiingereza")
        names_sw = has("swahili") or has("kiswahili")
        if names_en and not names_sw:
            return "en"
        if names_sw and not names_en:
            return "sw"
        # No direction given: flip from the previous answer's language, or,
        # with no previous answer at all, default to English (the only
        # direction that can be asked for without a prior Swahili answer).
        if last_language:
            return "en" if last_language == "sw" else "sw"
        return "en"
    return None


# Namespace for deterministic chunk ids. The table's id column is a UUID, so
# each chunk gets uuid5(namespace, "<source>:<name>"). Re-running an ingest
# script then REPLACES the same chunks instead of duplicating them, and never
# touches chunks from other sources (e.g. your PDFs).
_CHUNK_NAMESPACE = uuid.UUID("6f1d3c52-0b7a-4c1e-9a55-3f2b8e7d4a10")


def stable_id(key: str) -> str:
    return str(uuid.uuid5(_CHUNK_NAMESPACE, key))


# --- retrieval --------------------------------------------------------------

def get_store():
    # CPU by default: BGE-M3 on the GPU takes ~2 GB of the 6 GB, and llama3.1
    # needs ~4.7 GB, so together Ollama starts pushing layers to the CPU and
    # every answer gets slower. One short query embeds fine on the CPU.
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": os.getenv("EMBEDDING_DEVICE", "cpu")},
    )
    engine = PGEngine.from_connection_string(url=DATABASE_URL)
    return PGVectorStore.create_sync(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embeddings,
    )


def update_profile(profile: dict, entities: dict) -> dict:
    """Facts the user has told us that should survive into follow-up turns
    ("it's been 4 hours" shouldn't forget she said she's 3 months pregnant).
    A new stage replaces the old one and clears stale gestation numbers."""
    merged = dict(profile)
    if "stage" in entities and entities["stage"] != merged.get("stage"):
        merged.pop("gestational_month", None)
        merged.pop("gestational_week", None)
    for key in ("stage", "gestational_month", "gestational_week"):
        if key in entities:
            merged[key] = entities[key]
    return merged


# If the closest chunk is farther than this (cosine distance, lower = closer),
# the question is treated as NOT covered by the knowledge base and the model
# is not asked to answer it. Observed failure without this: "is a bit of
# alcohol bad at 3 months?" retrieved the sex-during-pregnancy chunk (nothing
# closer existed) and the model answered THAT question, in Swahili.
# Unset = guard off. Calibrate it with `python query.py` (it prints the
# distances): pick a value between your in-scope and out-of-scope questions.
_md = os.getenv("RETRIEVAL_MAX_DISTANCE", "").strip()
RETRIEVAL_MAX_DISTANCE = float(_md) if _md else None

# Fixed text, not model output. Still gives the safety net for anyone who
# phrased a real symptom in a way retrieval did not match.
NO_INFO = {
    "sw": "Samahani, sina taarifa za kutosha kuhusu swali hilo kwenye vyanzo vyangu. Tafadhali muulize mkunga, daktari au mhudumu wa afya. Ukiwa na dalili yoyote ya hatari au unajisikia vibaya, nenda kliniki au hospitali iliyo karibu mara moja.",
    "en": "Sorry, I don't have enough information about that in my sources. Please ask a midwife, doctor or health worker. If you have any danger sign or feel unwell, go to your nearest clinic or hospital right away.",
}

TRANSLATION_FAILED = {
    "sw": "Samahani, sikuweza kutafsiri jibu hilo kwa uhakika. Tafadhali uliza swali lako tena kwa Kiswahili. Ukijisikia vibaya, nenda kliniki au hospitali iliyo karibu mara moja.",
    "en": "Sorry, I couldn't translate that answer reliably. Please ask your question again in English. If you feel unwell, go to your nearest clinic or hospital right away.",
}

# Fixed, human-reviewed text appended to every high-risk answer, so the one
# instruction that matters does not depend on what the model wrote. HAVE A
# NATIVE SPEAKER / MIDWIFE REVIEW THE SWAHILI before real use. Kenya's
# emergency numbers are 999 and 112.
URGENT = {
    "sw": "MUHIMU: Hii inaweza kuwa dharura. Nenda kwenye kituo cha afya au hospitali iliyo karibu sasa hivi, au mwombe mtu akupeleke. Ukihitaji msaada wa haraka piga 999 au 112.",
    "en": "IMPORTANT: This could be an emergency. Go to the nearest health facility or hospital now, or ask someone to take you. If you need urgent help, call 999 or 112.",
}


def with_urgent(reply: str, language: str, risk_level: str) -> str:
    """Adds the fixed urgent line to high-risk answers (once)."""
    if risk_level != "high" or URGENT[language] in reply:
        return reply
    return f"{reply}\n\n{URGENT[language]}"


def _mt(text: str, target: str) -> str:
    from mt import translate_text  # lazy: loads the model on first use
    return translate_text(text, target)


def ensure_language(reply: str, target: str, mt=_mt) -> str:
    """Last line of defence on a freshly generated answer: if it came back in
    the wrong language (an English question answered in Swahili because the
    nearest source was Swahili), translate it. If translation also fails,
    return the original rather than nothing."""
    if detect_language(reply) == target:
        return reply
    try:
        out = mt(reply, target).strip()
    except Exception as e:  # model missing, out of memory, etc.
        print(f"[ensure_language] translation unavailable: {e}")
        return reply
    return out if out and detect_language(out) == target else reply


def translate_reply(history: dict, target: str, gen, risk_level: str = "low", mt=_mt):
    """Returns the previous answer in `target` language, or None if no
    attempt produced text actually in that language.

    Always translates the answer ALREADY GIVEN, never answers again:
    re-answering once produced the opposite advice ("still dangerous" in
    English, "not dangerous" in the Swahili re-answer). A dedicated
    translation model (mt.py) does the work. If it is unavailable, English
    can fall back to the LLM acting as translator; Swahili cannot (llama3.1
    produced nonsense), so it fails with a clear message instead.
    Every output is checked with detect_language() before it is accepted or
    cached. An earlier version cached an echoed, untranslated reply and
    returned it on every later request.
    `gen(system_prompt, user_message) -> str` is only used for that fallback."""
    replies = history["replies"]
    if target in replies:
        return replies[target]
    source = next(iter(replies.values()))

    candidates = []
    try:
        candidates.append(mt(source, target))
    except Exception as e:
        print(f"[translate_reply] MT unavailable: {e}")
        if target == "en":
            candidates.append(gen(build_translation_prompt("en"), source))

    for out in candidates:
        out = out.strip()
        if out and detect_language(out) == target:
            replies[target] = out
            return out
    return None


def _situation_instruction(profile: dict | None) -> str:
    if not profile:
        return ""
    stage = profile.get("stage")
    if stage == "pregnant":
        how_far = ""
        if "gestational_month" in profile:
            how_far = f", about {profile['gestational_month']} months along"
        elif "gestational_week" in profile:
            how_far = f", about {profile['gestational_week']} weeks along"
        return (
            f" The user has said she is currently pregnant{how_far}. The "
            "sources may also contain guidance for other situations (for "
            "example after giving birth). Use only the parts that apply to "
            "a woman who is still pregnant. Do NOT mention labour, delivery, "
            "giving birth, or the baby being born unless the user said that "
            "is happening."
        )
    if stage == "postpartum":
        return (
            " The user has said she has already given birth. Use only "
            "guidance that applies after birth."
        )
    return ""


def build_translation_prompt(target_language: str) -> str:
    """Translation is done on the ANSWER ALREADY GIVEN, not by answering the
    question again. Re-answering produced different medical advice from the
    first answer, and (because the question was still Swahili) often came
    back in Swahili anyway."""
    name = "English" if target_language == "en" else "Swahili"
    return (
        f"You are a careful translator. Translate the text the user sends "
        f"into {name}. Output ONLY the translation. Do not answer it, "
        "summarise it, or add anything: no new advice, symptoms, warnings or "
        "explanations. Keep every instruction and every urgency statement "
        "exactly as strong as in the original."
    )


def build_system_prompt(context: str, target_language: str, risk_level: str = "low",
                        profile: dict | None = None) -> str:
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
        # Added after real failures: asked about a painkiller, the model said
        # "yes, it is dangerous" with no source for it; asked about alcohol
        # (not in the sources then), it answered a different question.
        " Answer exactly the question that was asked. If the sources do not "
        "address it, say so plainly and tell the user to ask a midwife, "
        "doctor or pharmacist; do not answer a different question from the "
        "nearest source. Never say that a specific medicine, dose or "
        "substance is safe or unsafe unless the sources say so."
    )

    return (
        "You are a Swahili/English maternal health assistant. Answer the "
        "question using ONLY the information in the provided sources below. "
        "If the sources don't contain enough information to answer "
        "confidently, say so rather than guessing. "
        f"{language_instruction} Keep the answer short and simple, suitable "
        f"for someone with limited reading ability.{grounding_instruction}"
        f"{_situation_instruction(profile)}"
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
# Number can come before or after the unit in real speech/typing:
# "miezi 3", "3 months", "mimba ya miezi 3", "mwezi wa 3", "wiki 20", "20 weeks".
_WEEK_RE = re.compile(
    r"\b(?:wiki|weeks?)\s*(?:ya\s*|wa\s*)?(\d{1,2})\b|\b(\d{1,2})\s*(?:wiki|weeks?)\b",
    re.IGNORECASE,
)
_MONTH_RE = re.compile(
    r"\b(?:miezi|mwezi|months?)\s*(?:ya\s*|wa\s*)?(\d{1,2})\b|\b(\d{1,2})\s*(?:miezi|mwezi|months?)\b",
    re.IGNORECASE,
)

# Which situation the user is in. This matters because the knowledge base
# holds guidance for several (pregnancy, after birth) and retrieval can rank
# the wrong one first. A real observed failure: "I'm 3 months pregnant and
# have a bad headache" retrieved the POSTPARTUM danger signs first, and the
# model told her to go to the clinic "to give birth".
PREGNANT_MARKERS = ("mimba", "mjamzito", "ujauzito", "pregnant", "pregnancy")
POSTPARTUM_MARKERS = (
    "nimejifungua", "nilijifungua", "baada ya kujifungua", "after giving birth",
    "after birth", "gave birth", "postpartum", "have given birth",
)

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
        week = int(week_match.group(1) or week_match.group(2))
        if 1 <= week <= 42:
            entities["gestational_week"] = week

    month_match = _MONTH_RE.search(lowered)
    if month_match:
        month = int(month_match.group(1) or month_match.group(2))
        if 1 <= month <= 9:
            entities["gestational_month"] = month

    if any(m in lowered for m in POSTPARTUM_MARKERS):
        entities["stage"] = "postpartum"
    elif any(m in lowered for m in PREGNANT_MARKERS):
        entities["stage"] = "pregnant"

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
    candidates = store.similarity_search_with_score(search_query, k=CANDIDATE_K)
    scored = candidates[:TOP_K]
    results = [doc for doc, _ in scored]
    distances = [round(float(dist), 3) for _, dist in scored]

    # Risk comes from curated, intent-tagged chunks only (see CANDIDATE_K).
    risk_cutoff = RETRIEVAL_MAX_DISTANCE if RETRIEVAL_MAX_DISTANCE is not None else RISK_MAX_DISTANCE
    curated = [doc for doc, dist in candidates
               if doc.metadata.get("intent") and float(dist) <= risk_cutoff][:TOP_K]

    # Not covered by the knowledge base: nothing close enough. A self-harm
    # statement is never treated as "not covered".
    covered = bool(results)  # an empty knowledge base is "not covered" too
    if RETRIEVAL_MAX_DISTANCE is not None and distances:
        covered = min(distances) <= RETRIEVAL_MAX_DISTANCE
    if not covered and not any(m in question.lower() for m in SELF_HARM_MARKERS):
        return {
            "results": [],
            "context": "",
            "distances": distances,
            "covered": False,
            "classification": classify(question, []),
        }

    context = "\n\n".join(
        f"Source: {doc.metadata['source']} — {doc.metadata['heading']}\n{doc.page_content}"
        for doc in results
    )

    classification = classify(question, curated)

    return {
        "results": results,
        "context": context,
        "distances": distances,
        "covered": True,
        "classification": classification,
    }
