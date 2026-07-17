"""Rewrite the beats that check_tics.py flagged, so no phrasing is reused across books.

Why this exists (learned the hard way on book #4): you cannot prompt these away. We
de-templated the verdict prompt AND upgraded sonnet->opus, and the very next book still
opened a beat with "give the book real credit" — the exact phrase two earlier books used.
They aren't the prompt's skeleton, they're the MODEL's own book-reviewer idioms, and every
model in the family shares them. Detection + targeted rewrite beats hoping.

Free (Claude subscription), text-only, no credits. Run after `script`, before `narrate`.

Usage:
  python scripts/revise_tics.py             # rewrite flagged beats, loop until clean
  python scripts/revise_tics.py --dry-run   # show what it would rewrite
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_tics import find_books, grams, narration, distinctive  # noqa: E402
from cogni.config import load_config  # noqa: E402
from cogni.llm import call_stage  # noqa: E402

_SYSTEM = ("You are Cognibot, narrator of a channel that reads books so lazy humans don't have "
           "to. Blunt, a little funny, clear spoken English. You return only valid JSON.")

MAX_ROUNDS = 3


def flagged(slug: str, n: int = 5) -> dict[int, set[str]]:
    """{scene id: {reused phrase, ...}} vs every other book under projects/."""
    books = find_books()
    if slug not in books:
        raise SystemExit(f"[revise] {slug} has no scenes.json — run `script` first.")
    others = [x for x in books if x != slug]
    if not others:
        return {}
    _, cur_words = narration(books[slug])
    cur = grams(cur_words, n)
    prior: set[str] = set()
    for o in others:
        _, w = narration(books[o])
        prior |= set(grams(w, n))
    out: dict[int, set[str]] = defaultdict(set)
    for g, sid in cur.items():
        if g in prior and distinctive(g):
            out[sid].add(g)
    return dict(out)


def rewrite(cfg, narration_text: str, phrases: set[str]) -> str:
    banned = "\n".join(f'  - "{p}"' for p in sorted(phrases))
    prompt = (
        f"This line is from a Cognibot video:\n\n{narration_text}\n\n"
        f"It reuses phrasing that already appeared in OUR OWN earlier videos:\n{banned}\n\n"
        f"Rewrite the line so it makes exactly the same point, in the same voice, at the same "
        f"length — but shares NONE of that phrasing. Say the thing a different way: change the "
        f"image, the sentence shape, the way the judgement is framed. Do not simply swap a "
        f"synonym into the same sentence skeleton.\n\n"
        f'Return JSON: {{"narration": "<the rewritten line>"}}'
    )
    data = call_stage(cfg, "script", prompt, system=_SYSTEM, json_out=True)
    new = (data.get("narration") or "").strip()
    if not new:
        raise RuntimeError("model returned no narration")
    return new


def contains_any(text: str, phrases: set[str]) -> list[str]:
    """A phrase 'hits' if its words appear consecutively in the normalized text."""
    import re
    t = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    t = " " + re.sub(r"\s+", " ", t) + " "
    return [p for p in phrases if f" {p} " in t]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = load_config()
    slug = (REPO / ".active_project").read_text(encoding="utf-8").strip()
    scenes_path = REPO / "projects" / slug / "scenes.json"

    for rnd in range(1, MAX_ROUNDS + 1):
        hits = flagged(slug)
        if not hits:
            print(f"[revise] CLEAN — no phrasing reused from other books.")
            return
        print(f"[revise] round {rnd}: {len(hits)} beat(s) reuse phrasing "
              f"({sum(len(v) for v in hits.values())} phrase(s))")
        if a.dry_run:
            for sid, ps in sorted(hits.items()):
                print(f"  scene {sid}: {sorted(ps)}")
            print("[revise] dry run — nothing written.")
            return

        doc = json.loads(scenes_path.read_text(encoding="utf-8"))
        by = {s["id"]: s for s in doc["scenes"]}
        fixed = 0
        for sid, phrases in sorted(hits.items()):
            old = by[sid].get("narration") or ""
            try:
                new = rewrite(cfg, old, phrases)
            except Exception as e:
                print(f"  scene {sid:>3}: FAILED ({str(e)[:60]}) — left as-is")
                continue
            still = contains_any(new, phrases)
            if still:
                print(f"  scene {sid:>3}: rewrite still contains {still} — left as-is")
                continue
            by[sid]["narration"] = new
            fixed += 1
            print(f"  scene {sid:>3}: rewritten")
            print(f"        was: {old[:90]}...")
            print(f"        now: {new[:90]}...")
        scenes_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print(f"[revise] round {rnd}: rewrote {fixed}/{len(hits)} beat(s)")
        if fixed == 0:
            print("[revise] no progress this round — fix the remaining beats by hand.")
            return

    print(f"[revise] hit the {MAX_ROUNDS}-round limit — run check_tics.py to see what's left.")


if __name__ == "__main__":
    main()
