"""
CLI front end for your own testing — the actual retrieval, language, and
generation logic all live in rag_core.py now, shared with service.py (the
HTTP service the backend actually talks to). This file just drives that
shared logic from a terminal, with streaming output so you can see tokens
arrive live.

Language policy:
  - Pure English question  -> answer in English
  - Pure Swahili question  -> answer in Swahili
  - Mixed/code-switched    -> answer in Swahili (the default audience)
  - "can you say that in English?" (or similar) -> re-answers the PREVIOUS
    question in English, from the same retrieved sources.

Usage:
    python query.py "Nina maumivu makali ya kichwa, nifanye nini?"   # one-shot
    python query.py                                                  # interactive
"""
import sys

from rag_core import (
    NO_INFO,
    NOTHING_TO_TRANSLATE,
    TRANSLATION_FAILED,
    generate_text,
    build_system_prompt,
    detect_language,
    ensure_language,
    generate_stream,
    get_store,
    requested_translation_language,
    retrieve,
    translate_reply,
    update_profile,
    with_urgent,
)


def generate(system_prompt: str, user_question: str) -> str:
    # stream=True (inside generate_stream) is on purpose: a non-streaming
    # call prints nothing until the whole answer is ready, which looks
    # identical to a genuine hang if Ollama is slow to load the model (it
    # unloads after ~5 min idle) or is stuck. Streaming means the first
    # token appearing is proof it's actually working.
    print("--- Answer --- (generating; first run / cold model load can take a while)")
    pieces = []
    for piece in generate_stream(system_prompt, user_question):
        print(piece, end="", flush=True)
        pieces.append(piece)
    print()
    return "".join(pieces)


def answer_question(store, question: str, history: dict) -> None:
    """`history` carries the last retrieved context + question + response
    language + classification across turns, so a translation follow-up
    doesn't need to re-run retrieval."""

    translation_target = requested_translation_language(
        question, history.get("last_language")
    )
    if translation_target:
        replies = history.get("replies")
        if not replies:
            print(NOTHING_TO_TRANSLATE[translation_target])
            print("(Tip: translation needs an earlier answer in the SAME run. "
                  "Use interactive mode: `python query.py` with no arguments.)")
            return
        reply = translate_reply(
            history, translation_target, generate_text, history.get("risk_level", "low")
        )
        if reply is None:
            print(TRANSLATION_FAILED[translation_target])
            return
        print(reply)
        history["last_language"] = translation_target
        return

    target_language = detect_language(question)

    retrieved = retrieve(store, question, prior_question=history.get("question"))
    results = retrieved["results"]
    distances = retrieved["distances"]

    # Distances are printed so you can calibrate RETRIEVAL_MAX_DISTANCE:
    # lower = closer. Note the best (smallest) number for questions the
    # knowledge base DOES cover vs ones it doesn't, and set the threshold
    # between them.
    print("--- Retrieved sources (cosine distance, lower = closer) ---")
    docs_for_print = results or []
    if docs_for_print:
        for doc, dist in zip(docs_for_print, distances):
            print(f"  {dist:.3f}  [{doc.metadata['source']}] {doc.metadata['heading']}")
    else:
        print(f"  best distances: {distances}  (all beyond RETRIEVAL_MAX_DISTANCE)")

    classification = retrieved["classification"]
    print(
        f"--- Classification --- intent={classification['intent']} "
        f"risk_level={classification['risk_level']} "
        f"escalate={classification['escalate']} "
        f"entities={classification['entities']}"
    )
    print()

    profile = update_profile(history.get("profile", {}), classification["entities"])
    if not retrieved["covered"]:
        reply = NO_INFO[target_language]
        print("--- Answer ---")
        print(reply)
    else:
        system_prompt = build_system_prompt(
            retrieved["context"], target_language, classification["risk_level"], profile
        )
        reply = generate(system_prompt, question)
        fixed = ensure_language(reply, target_language)
        if fixed != reply:
            print(f"\n(Answer came back in the wrong language; translated to "
                  f"{'English' if target_language == 'en' else 'Swahili'}:)")
            print(fixed)
            reply = fixed

    if retrieved["covered"]:
        extra = with_urgent("", target_language, classification["risk_level"]).strip()
        if extra:
            print("\n" + extra)

    history["context"] = retrieved["context"]
    history["question"] = question
    history["last_language"] = target_language
    history["risk_level"] = classification["risk_level"]
    history["profile"] = profile
    history["replies"] = {target_language: reply}


def main():
    store = get_store()
    history: dict = {}

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        answer_question(store, question, history)
        return

    print("Interactive mode. Type a question, or 'quit' to exit.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question or question.lower() in ("quit", "exit"):
            break
        answer_question(store, question, history)


if __name__ == "__main__":
    main()
