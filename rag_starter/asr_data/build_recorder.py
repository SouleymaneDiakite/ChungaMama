"""Embeds prompts.json into recorder_template.html -> recorder.html (one self-contained file)."""
import json
tpl = open("recorder_template.html", encoding="utf-8").read()
prompts = open("prompts.json", encoding="utf-8").read()
open("recorder.html", "w", encoding="utf-8").write(tpl.replace("__PROMPTS__", prompts))
print("wrote recorder.html")
