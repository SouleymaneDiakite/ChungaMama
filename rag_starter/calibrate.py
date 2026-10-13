"""
Finds a RETRIEVAL_MAX_DISTANCE that separates questions the knowledge base
covers from ones it doesn't, using YOUR data (embedding distances depend on
what is in the table, so a threshold can't be chosen in advance).

    python calibrate.py

Edit IN_SCOPE / OUT_OF_SCOPE below: add real questions you expect, especially
borderline ones. The more honest the lists, the more the result means.
It prints each question's best (smallest) distance, then either a threshold
that cleanly separates the two groups, or a clear statement that none does.
"""
from rag_core import TOP_K, get_store

# Questions the knowledge base should be able to answer (any language).
IN_SCOPE = [
    "Nina maumivu makali ya kichwa, nifanye nini?",
    "my wife has been bleeding for a month since giving birth. Should I take her to the hospital?",
    "When should I start clinic visits? I just got pregnant",
    "Is drinking a bit of alcohol bad when you are 3 months pregnant?",
    "Naweza kunywa pombe kidogo nikiwa mjamzito?",
    "Can I take painkillers while pregnant?",
    "Ni chanjo gani mtoto anapaswa kupata akizaliwa?",
    "What should I eat while pregnant?",
    "Ni vyakula gani vinafaa kwa mama mjamzito?",
    "Is it safe to have sex during pregnancy?",
    "Nimekuwa na huzuni sana tangu nijifungue",
    "How can the father support the mother after birth?",
    "Mtoto wangu hanyonyi vizuri, nifanye nini?",
    "Nipange nini kabla ya kujifungua?",
]

# Clearly unrelated questions. The assistant should say "I don't have information".
OUT_OF_SCOPE = [
    "What are some businesses I can start with a capital of KES 10K?",
    "Who won the football match yesterday?",
    "How do I fix a flat tyre?",
    "Ni bei gani ya simu mpya?",
    "Write me a poem about the sea",
    "What is the capital of France?",
    "How do I bake a cake?",
]

# Medical but NOT about mothers/babies. The hard cases: same vocabulary
# domain, so these are the ones most likely to overlap with in-scope.
NEAR_DOMAIN_OUT_OF_SCOPE = [
    "How do I treat a snake bite?",
    "What diet is good for an adult with diabetes?",
    "Nina maumivu ya goti, nifanye nini?",
    "How do I treat malaria in an adult man?",
]


def best(store, q):
    return min(float(d) for _, d in store.similarity_search_with_score(q, k=TOP_K))


def main():
    store = get_store()
    groups = {
        "IN SCOPE": IN_SCOPE,
        "OUT OF SCOPE": OUT_OF_SCOPE,
        "NEAR-DOMAIN OUT OF SCOPE": NEAR_DOMAIN_OUT_OF_SCOPE,
    }
    scores = {}
    for name, qs in groups.items():
        print(f"\n== {name} ==")
        scores[name] = []
        for q in qs:
            d = best(store, q)
            scores[name].append(d)
            print(f"  {d:.3f}  {q}")

    worst_in = max(scores["IN SCOPE"])
    best_out = min(scores["OUT OF SCOPE"])
    best_near = min(scores["NEAR-DOMAIN OUT OF SCOPE"])
    print("\n== RESULT ==")
    print(f"farthest in-scope question : {worst_in:.3f}")
    print(f"closest unrelated question : {best_out:.3f}")
    print(f"closest near-domain question: {best_near:.3f}")

    if worst_in < best_out:
        t = (worst_in + best_out) / 2
        print(f"\nUnrelated questions separate cleanly. Suggested threshold: {t:.3f}")
        print(f"  Add to rag_starter/.env:  RETRIEVAL_MAX_DISTANCE={t:.3f}")
        margin = best_out - worst_in
        if margin < 0.05:
            print(f"  WARNING: margin is only {margin:.3f}. Fragile on questions you haven't "
                  "tested; add more questions above, or use a reranker.")
        if best_near <= t:
            print("  NOTE: near-domain questions (snake bite, diabetes...) still pass this "
                  "threshold, so those will reach the model. The prompt tells it to say "
                  "'not in my sources', but the distance gate alone won't stop them.")
    else:
        bad_in = [q for q, d in zip(IN_SCOPE, scores["IN SCOPE"]) if d >= best_out]
        bad_out = [q for q, d in zip(OUT_OF_SCOPE, scores["OUT OF SCOPE"]) if d <= worst_in]
        print("\nNo single distance separates in-scope from unrelated questions.")
        print("In-scope questions that look 'farther' than some unrelated ones:")
        for q in bad_in:
            print("  -", q)
        print("Unrelated questions that look 'closer' than some in-scope ones:")
        for q in bad_out:
            print("  -", q)
        print("\nDo NOT set RETRIEVAL_MAX_DISTANCE from this: it would block real "
              "questions or let unrelated ones through. Next step: a reranker "
              "(cross-encoder) as the relevance gate.")


if __name__ == "__main__":
    main()
