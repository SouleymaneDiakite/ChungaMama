"""
After recording: checks every clip and writes train/valid manifests for Colab.

    python build_manifest.py recordings/        # folder holding <id>.wav + <id>.txt

Outputs (next to the recordings folder):  train.jsonl, valid.jsonl
Each line: {"audio": "<id>.wav", "text": "...", "lang": "sw|en|cs", "whisper_lang": "sw|en", "seconds": 23.4}
Valid split = 12% (every 8th clip within each language set), so all three sets are represented.
"""
import json, random, sys, wave
from pathlib import Path

folder = Path(sys.argv[1] if len(sys.argv) > 1 else "recordings")
out = folder.parent
bad, rows = [], []
for wav in sorted(folder.glob("*.wav")):
    txt = wav.with_suffix(".txt")
    if not txt.exists(): bad.append((wav.name, "no .txt")); continue
    text = txt.read_text(encoding="utf-8").strip()
    with wave.open(str(wav)) as w:
        secs = w.getnframes() / w.getframerate()
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (16000, 1, 2):
            bad.append((wav.name, "not 16 kHz mono 16-bit")); continue
    if not text: bad.append((wav.name, "empty transcript")); continue
    if secs > 30: bad.append((wav.name, f"{secs:.1f}s > 30s")); continue
    if secs < 8: bad.append((wav.name, f"{secs:.1f}s is very short")); continue
    lang = wav.stem.split("_")[0]
    rows.append({"audio": wav.name, "text": text, "lang": lang,
                 "whisper_lang": "en" if lang == "en" else "sw",   # code-switched clips use the Swahili token
                 "seconds": round(secs, 2)})

random.Random(1).shuffle(rows)
valid, train, seen = [], [], {}
for r in rows:
    seen[r["lang"]] = seen.get(r["lang"], 0) + 1
    (valid if seen[r["lang"]] % 8 == 0 else train).append(r)
for name, data in (("train.jsonl", train), ("valid.jsonl", valid)):
    (out / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in data) + "\n", encoding="utf-8")

hours = sum(r["seconds"] for r in rows) / 3600
print(f"{len(rows)} good clips ({hours:.2f} h): train {len(train)}, valid {len(valid)}")
for l in ("sw", "en", "cs"): print(f"  {l}: {seen.get(l, 0)}")
for n, why in bad: print("  PROBLEM", n, why)
