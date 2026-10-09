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
    NOTHING_TO_TRANSLATE,
    build_system_prompt,
    detect_language,
    generate_stream,
    get_store,
    requested_translation_language,
    retrieve,
)


def generate(system_prompt: str, user_question: str) -> None:
    # stream=True (inside generate_stream) is on purpose: a non-streaming
    # call prints nothing until the whole answer is ready, which looks
    # identical to a genuine hang if Ollama is slow to load the model (it
    # unloads after ~5 min idle) or is stuck. Streaming means the first
    # token appearing is proof it's actually working.
    print("--- Answer --- (generating; first run / cold model load can take a while)")
    for piece in generate_stream(system_prompt, user_question):
        print(piece, end="", flush=True)
    print()


def answer_question(store, question: str, history: dict) -> None:
    """`history` carries the last retrieved context + question + response
    language + classification across turns, so a translation follow-up
    doesn't need to re-run retrieval."""

    translation_target = requested_translation_language(
        question, history.get("last_language")
    )
    if translation_target and not history.get("context"):
        print(NOTHING_TO_TRANSLATE[translation_target])
        print("(Tip: translation needs an earlier answer in the SAME run. "
              "Use interactive mode: `python query.py` with no arguments.)")
        return
    if translation_target:
        system_prompt = build_system_prompt(
            history["context"], translation_target, history.get("risk_level", "low")
        )
        generate(system_prompt, history["question"])
        history["last_language"] = translation_target
        return

    target_language = detect_language(question)

    retrieved = retrieve(store, question, prior_question=history.get("question"))
    results = retrieved["results"]

    if not results:
        print("No relevant guidance found in the knowledge base.")
        return

    print("--- Retrieved sources ---")
    for doc in results:
        print(f"  [{doc.metadata['source']}] {doc.metadata['heading']}")

    classification = retrieved["classification"]
    print(
        f"--- Classification --- intent={classification['intent']} "
        f"risk_level={classification['risk_level']} "
        f"escalate={classification['escalate']} "
        f"entities={classification['entities']}"
    )
    print()

    system_prompt = build_system_prompt(
        retrieved["context"], target_language, classification["risk_level"]
    )
    generate(system_prompt, question)

    history["context"] = retrieved["context"]
    history["question"] = question
    history["last_language"] = target_language
    history["risk_level"] = classification["risk_level"]


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
