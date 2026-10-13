# ASR recording kit (SunflowerASR fine-tuning data)

500 prompts: 200 Swahili (`sw_`), 200 English (`en_`), 100 code-switched (`cs_`), each reads in about 19-27 s.

1. Open `recorder.html` in Chrome or Edge (double-click is fine).
2. Click **Choose save folder** and pick `asr_data/recordings/`. Clips save as `<id>.wav` + `<id>.txt` (16 kHz mono 16-bit). Re-opening and choosing the same folder resumes where you stopped.
3. Keys: R record/stop, P play, S skip, Enter save. If you misread a word, **edit the text to what you actually said** before saving.
4. Quiet room, same mic distance, read naturally. Several speakers is better than one.
5. `python build_manifest.py recordings/` checks every clip and writes `train.jsonl` / `valid.jsonl` (88/12 split) for Colab.

Without folder access (other browsers) clips download instead; Chrome asks once to allow multiple downloads.
Never commit `recordings/` (voice data).
