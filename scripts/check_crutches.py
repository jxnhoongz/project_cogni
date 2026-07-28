"""Flag WITHIN-script crutches the reviews called out: the word "honest" overused, and
fixed-skeleton phrases ("here's my honest take", "X years later", "who this is for", "in
this video"). Cross-BOOK reuse is check_tics.py; mispronunciations are check_pronunciation.py.

Run after `script`, before `narrate`. Free, text-only.

Usage:  python scripts/check_crutches.py [--honest-max 3]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

_HONEST = re.compile(r"\bhonest(ly)?\b", re.I)
_SKELETON = [
    re.compile(r"\bhere'?s my (honest )?(take|gripe|read|flag)\b", re.I),
    re.compile(r"\b(in this video|what this book (really )?wants)\b", re.I),
    re.compile(r"\bwho (this|it|the book) (is|really is) (for|not for)\b|\bwho (is|really is) (this|it|the book|this book) (for|not for)\b|\bwho should (skip|read)\b", re.I),
    re.compile(r"\b(a year|two years|three years|five years|six months|months|years) (later|after)\b", re.I),
]


def find_crutches(scenes: list[dict], honest_max: int = 3) -> dict:
    honest_hits, total = [], 0
    skeleton = []
    for s in scenes:
        n = s.get("narration") or ""
        c = len(_HONEST.findall(n))
        if c:
            honest_hits.append((s["id"], c)); total += c
        for pat in _SKELETON:
            if pat.search(n):
                skeleton.append((s["id"], pat.search(n).group(0))); break
    return {"honest": honest_hits if total > honest_max else [], "skeleton": skeleton}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--honest-max", type=int, default=3)
    a = ap.parse_args()
    slug = (REPO / ".active_project").read_text(encoding="utf-8").strip()
    scenes = json.loads((REPO / "projects" / slug / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    out = find_crutches(scenes, a.honest_max)
    if not out["honest"] and not out["skeleton"]:
        print(f"[crutches] {slug}: PASS — no 'honest' overuse or skeleton phrases.")
        return
    if out["honest"]:
        tot = sum(c for _, c in out["honest"])
        print(f"[crutches] 'honest/honestly' used {tot}x (max {a.honest_max}) — cut most; be incisive, don't announce it:")
        for sid, c in out["honest"]:
            print(f"  scene {sid:>3}  x{c}")
    if out["skeleton"]:
        print(f"[crutches] {len(out['skeleton'])} skeleton phrase(s) — vary these so episodes don't feel identical:")
        for sid, ph in out["skeleton"]:
            print(f'  scene {sid:>3}  "{ph}"')
    print("\n[crutches] Rewrite those beats in scenes.json, then re-run.")


if __name__ == "__main__":
    main()
