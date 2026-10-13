"""
Speech-to-text seam: transcribe(audio_path, language) -> text.

Loads the WAV with soundfile and hands the samples to the model, so ffmpeg is
NOT needed (passing a filename to the transformers pipeline needs ffmpeg).
The frontend sends 16 kHz mono WAV.

SunflowerASR is Whisper large-v3 and is GATED on Hugging Face. Before first use:
  1. Accept the terms on the model page while logged in.
  2. Run `huggingface-cli login` (or set HF_TOKEN).

The language token MUST be forced (the model card says passing a Whisper
language name is not enough). Token ids below are from the model card table.
To swap in your own fine-tuned checkpoint, change ASR_MODEL only.

Env:
  ASR_MODEL   default Sunbird/SunflowerASR-51-african-languages
  ASR_DEVICE  cpu (default) | cuda. CPU is the default because llama3.1 needs
              the 6 GB GPU; large-v3 in fp16 would not fit beside it.
Loads lazily on the first call; the first call downloads ~3 GB.
"""
import os
import threading

import numpy as np

ASR_MODEL = os.getenv("ASR_MODEL", "Sunbird/SunflowerASR-51-african-languages")
ASR_DEVICE = os.getenv("ASR_DEVICE", "cpu").strip().lower()

# From the model card's language-token table (these are Whisper's own ids).
LANGUAGE_TOKENS = {"sw": 50318, "en": 50259}

_state = None
_lock = threading.Lock()


def _load():
    global _state
    with _lock:
        if _state is None:
            import torch
            from transformers import WhisperForConditionalGeneration, WhisperProcessor

            use_gpu = ASR_DEVICE == "cuda" and torch.cuda.is_available()
            dtype = torch.float16 if use_gpu else torch.float32
            processor = WhisperProcessor.from_pretrained(ASR_MODEL)
            model = WhisperForConditionalGeneration.from_pretrained(ASR_MODEL, torch_dtype=dtype)
            model.to("cuda" if use_gpu else "cpu").eval()
            _state = (processor, model, dtype, "cuda" if use_gpu else "cpu")
        return _state


def _read_audio(path: str) -> np.ndarray:
    import soundfile as sf

    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:  # the app already sends 16 kHz; this is for ad-hoc CLI tests
        n = int(round(len(audio) * 16000 / sr))
        audio = np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype("float32")
    return audio


def transcribe(audio_path: str, language: str = "sw") -> str:
    """Transcript of a clip (30 s max). language: "sw" (also use for
    code-switched speech) or "en"."""
    import torch

    processor, model, dtype, device = _load()
    tok = processor.tokenizer
    lang_id = LANGUAGE_TOKENS.get(language, LANGUAGE_TOKENS["sw"])
    forced = [
        (1, lang_id),
        (2, tok.convert_tokens_to_ids("<|transcribe|>")),
        (3, tok.convert_tokens_to_ids("<|notimestamps|>")),
    ]
    audio = _read_audio(audio_path)[: 16000 * 30]
    feats = processor(audio, sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad():
        ids = model.generate(
            feats.to(device, dtype),
            forced_decoder_ids=forced,
            num_beams=1,
            do_sample=False,
            max_new_tokens=440,
        )
    return processor.batch_decode(ids, skip_special_tokens=True)[0].strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) not in (2, 3):
        print("Usage: python asr.py clip.wav [sw|en]")
        raise SystemExit(1)
    print(transcribe(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "sw"))
