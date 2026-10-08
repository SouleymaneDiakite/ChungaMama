"""
Text-to-speech, Phase 5 of the project plan: cheapest possible
implementation behind one function, so a better/offline voice later
doesn't touch anything that calls speak().

gTTS (Google's free web TTS) chosen because it needs no model download,
no GPU, and supports both Swahili ("sw") and English ("en") out of the
box — the two languages query.py/service.py ever ask for. Downsides,
honestly: it requires internet access (it calls a Google endpoint), and
voice quality/naturalness is noticeably more robotic than a real trained
TTS model. That's an acceptable trade for an MVP; if that becomes a real
problem (voice quality, or needing this to work offline), the fix is
swapping the inside of speak() for Coqui TTS or a fine-tuned model —
nothing outside this file needs to change either way.

Usage:
    from tts import speak
    speak("Nenda kliniki mara moja.", "sw", "answer.mp3")
"""
from gtts import gTTS


def speak(text: str, language: str, output_path: str) -> str:
    """language is 'sw' or 'en' — the same two values detect_language()
    and build_system_prompt() in rag_core.py already use, so callers don't
    need to translate between two different language-code conventions."""
    if language not in ("sw", "en"):
        raise ValueError(f"Unsupported language: {language!r} (expected 'sw' or 'en')")

    tts = gTTS(text=text, lang=language)
    tts.save(output_path)
    return output_path


if __name__ == "__main__":
    # Quick manual check: `python tts.py` makes two short sample clips.
    speak("Nenda kliniki mara moja.", "sw", "sample_sw.mp3")
    speak("Please go to the clinic immediately.", "en", "sample_en.mp3")
    print("Wrote sample_sw.mp3 and sample_en.mp3 — play them to confirm audio quality.")
