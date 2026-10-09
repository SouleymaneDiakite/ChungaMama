"""
Speech-to-text seam: transcribe(audio_path) -> text.

Uses the same pipeline call that won the Colab comparison against Paza
(Sunbird/SunflowerASR-51-african-languages). To swap models later (e.g. your
own fine-tuned checkpoint), change ASR_MODEL only; nothing else calls the
model directly.

SunflowerASR is GATED on Hugging Face. Before first use on this machine:
  1. Accept the terms on the model page while logged in.
  2. Run `huggingface-cli login` (or set HF_TOKEN in the environment).

The model loads lazily on the first call (not at service startup), so the
chat endpoint starts fast and users who never use voice don't pay for it.
First call downloads the weights and takes a while.
"""
import threading

ASR_MODEL = "Sunbird/SunflowerASR-51-african-languages"

_pipeline = None
_lock = threading.Lock()


def _get_pipeline():
    global _pipeline
    with _lock:
        if _pipeline is None:
            import torch
            from transformers import pipeline

            use_gpu = torch.cuda.is_available()
            _pipeline = pipeline(
                "automatic-speech-recognition",
                model=ASR_MODEL,
                device=0 if use_gpu else -1,
                torch_dtype=torch.float16 if use_gpu else torch.float32,
            )
        return _pipeline


def transcribe(audio_path: str) -> str:
    """Returns the transcript of an audio file. The frontend sends 16 kHz
    mono WAV, which the pipeline reads directly without needing ffmpeg."""
    asr = _get_pipeline()
    out = asr(audio_path)
    return out["text"].strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python asr.py path/to/audio.wav")
        raise SystemExit(1)
    print(transcribe(sys.argv[1]))
