"""Flag words the TTS narrator mispronounces, in the active book's narration.

Run after `script`, before `narrate` (same slot as check_tics.py). Reports scene ids so
the beats get rephrased before they're baked into audio + burned subtitles. The word list
lives in cogni/pronounce.py — grow it as new mispronunciations are heard.

Usage:  python scripts/check_pronunciation.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from cogni.pronounce import TTS_AVOID  # noqa: E402


def main() -> None:
    slug = (REPO / ".active_project").read_text(encoding="utf-8").strip()
    scenes = json.loads((REPO / "projects" / slug / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    pats = {w: re.compile(rf"\b{re.escape(w)}\b", re.I) for w in TTS_AVOID}

    hits = []
    for s in scenes:
        n = s.get("narration") or ""
        for w, pat in pats.items():
            if pat.search(n):
                hits.append((s["id"], w, n))
    if not hits:
        print(f"[pron] {slug}: PASS — no known-mispronounced words in narration.")
        return
    print(f"[pron] {slug}: {len(hits)} beat(s) use a mispronounced word — rephrase before narrate:\n")
    for sid, w, n in hits:
        print(f"  scene {sid:>3}  \"{w}\"  — {TTS_AVOID[w]}")
    print("\n[pron] Rewrite those beats in scenes.json, then re-run.")


if __name__ == "__main__":
    main()
