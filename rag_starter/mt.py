"""
Machine translation seam: translate_text(text, target) -> text, target in
{"en", "sw"}.

Why a separate model: llama3.1 (8B) is not reliable at English -> Swahili.
Observed failures were a translation that turned "don't wait for any
symptoms" into roughly "don't forget to follow symptoms", and a re-answer
that said "not dangerous" where the English answer said "still dangerous".
NLLB-200 is a model trained specifically for translation and covers Swahili.
It is still a model, so the same rule applies: check outputs by eye on the
phrases that matter (danger signs, "go to the clinic now").

To swap models later (e.g. a larger NLLB, or a Sunbird translation model),
change MT_MODEL; nothing else calls the model directly.

It runs on the CPU by default (MT_DEVICE=cpu). The GPU's 6 GB is already
mostly taken by llama3.1 in Ollama; putting this model there too would push
Ollama's layers onto the CPU and slow every answer down. A few short
sentences translate in a couple of seconds on CPU. Set MT_DEVICE=cuda if you
have VRAM to spare.

The model loads on the first call (not at service startup).
"""
import os
import re
import threading

MT_MODEL = os.getenv("MT_MODEL", "facebook/nllb-200-distilled-1.3B")
MT_DEVICE = os.getenv("MT_DEVICE", "cpu")

_CODES = {"en": "eng_Latn", "sw": "swh_Latn"}

_tokenizer = None
_model = None
_lock = threading.Lock()


def _load():
    global _tokenizer, _model
    with _lock:
        if _model is None:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            _tokenizer = AutoTokenizer.from_pretrained(MT_MODEL)
            _model = AutoModelForSeq2SeqLM.from_pretrained(MT_MODEL).to(MT_DEVICE)
            _model.eval()
    return _tokenizer, _model


def _split_sentences(text: str) -> list[str]:
    # NLLB translates best one sentence at a time; long paragraphs lose
    # clauses. Split on sentence ends and newlines, keep the order.
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def translate_text(text: str, target: str) -> str:
    import torch

    if target not in _CODES:
        raise ValueError(f"unsupported target language: {target!r}")
    source = "sw" if target == "en" else "en"
    tokenizer, model = _load()
    tokenizer.src_lang = _CODES[source]

    out = []
    for sentence in _split_sentences(text):
        inputs = tokenizer(sentence, return_tensors="pt", truncation=True, max_length=256)
        inputs = {k: v.to(MT_DEVICE) for k, v in inputs.items()}
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(_CODES[target]),
                max_new_tokens=256,
                num_beams=4,
            )
        out.append(tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip())
    return " ".join(out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3 or sys.argv[1] not in _CODES:
        print('Usage: python mt.py en|sw "text to translate INTO that language"')
        raise SystemExit(1)
    print(translate_text(sys.argv[2], sys.argv[1]))
