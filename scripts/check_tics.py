"""Cross-book tic checker — catch the writer reusing phrasing across videos.

Run AFTER `script`, BEFORE `narrate`. Compares the active project's narration against
every other book's narration and reports distinctive phrases that appear in both, with
the scene ids to fix. Free, text-only, no credits.

Why this exists: books 1-3 shipped with the same verdict scaffolding recycled across
videos ("as an instruction manual", "the single best idea in the whole book", "give the
book real credit"). The root cause (a prompt that enumerated a fixed set of verdict
moves) is fixed, but LLMs have favourite phrasings — this is the mechanical net under it.
A viewer who watches two videos feels the template even if they can't name it.

Usage:
  python scripts/check_tics.py            # active project vs all others
  python scripts/check_tics.py --n 5      # phrase length (default 5 words)
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROJECTS = REPO / "projects"

# words that make a phrase generic rather than a distinctive tic
_FILLER = re.compile(
    r"^(and|but|the|a|an|to|of|it|its|that|this|you|your|i|my|we|he|his|him|she|her|they|them|"
    r"is|are|was|were|be|been|am|s|t|m|re|ve|d|ll|in|on|at|as|with|for|from|by|so|if|or|not|no|"
    r"do|does|did|have|has|had|will|would|can|could|just|like|what|when|then|than|there|here|"
    r"now|out|up|all|about|into|more|most|some|any|one|two|thing|things|really|actually)$"
)


def find_books() -> dict[str, Path]:
    """{book name: scenes.json} for every book under projects/, AT ANY DEPTH.

    Must be recursive: finished books get filed into subfolders (e.g. projects/Uploaded/).
    A non-recursive scan silently reports "nothing to check" once that happens — a false
    pass, which is worse than no check at all.
    """
    return {f.parent.name: f for f in PROJECTS.rglob("scenes.json")}


def narration(p: Path) -> tuple[str, list[tuple[str, int]]]:
    """Flattened narration text + [(word, scene id)] for a book's scenes.json."""
    if not p.exists():
        return "", []
    doc = json.loads(p.read_text(encoding="utf-8"))
    words, where = [], {}
    for s in doc.get("scenes", []):
        t = (s.get("narration") or "").lower()
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        for w in t.split():
            words.append((w, s["id"]))
    return " ".join(w for w, _ in words), words  # type: ignore[return-value]


def grams(words: list[tuple[str, int]], n: int) -> dict[str, int]:
    """{phrase: first scene id it appears in}"""
    out: dict[str, int] = {}
    for i in range(len(words) - n + 1):
        chunk = words[i:i + n]
        g = " ".join(w for w, _ in chunk)
        out.setdefault(g, chunk[0][1])
    return out


def distinctive(g: str) -> bool:
    """Real tics carry >=2 content words, at least one of them substantial.

    >=3 was too strict: it dropped "as an instruction manual" (only `instruction` +
    `manual` are content words) — one of the actual tics shipped in two books. This is
    a surfacing tool: a few false positives are cheap, a missed tic ships.
    """
    content = [w for w in g.split() if not _FILLER.match(w)]
    return len(content) >= 2 and any(len(w) >= 6 for w in content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5, help="phrase length in words")
    a = ap.parse_args()

    slug = (REPO / ".active_project").read_text(encoding="utf-8").strip()
    books = find_books()
    if slug not in books:
        raise SystemExit(f"[tics] {slug} has no scenes.json — run `script` first.")
    others = sorted(n for n in books if n != slug)
    if not others:
        print("[tics] no other books found under projects/ — nothing to compare against.\n"
              "[tics] (If you have finished books, check they're still under projects/ — "
              "this scan is recursive, so subfolders are fine.)")
        return

    _, cur_words = narration(books[slug])
    if not cur_words:
        raise SystemExit(f"[tics] {slug} has no narration — run `script` first.")
    cur = grams(cur_words, a.n)

    prior: dict[str, set[str]] = defaultdict(set)
    for o in others:
        _, w = narration(books[o])
        for g in grams(w, a.n):
            prior[g].add(o)

    shared = {g: (sid, prior[g]) for g, sid in cur.items() if g in prior and distinctive(g)}

    print(f"[tics] {slug}: {len(cur):,} distinct {a.n}-word phrases; "
          f"compared against {len(others)} book(s): {', '.join(others)}")
    if not shared:
        print(f"[tics] PASS — no distinctive phrasing reused from other books.")
        return
    print(f"[tics] {len(shared)} REUSED phrase(s) — rewrite these beats before `narrate`:\n")
    for g, (sid, books) in sorted(shared.items(), key=lambda kv: kv[1][0]):
        print(f'  scene {sid:>3}  "{g}"')
        print(f'            also in: {", ".join(sorted(books))}')
    print(f"\n[tics] These are the lines a repeat viewer will feel as a template. "
          f"Rewrite them in scenes.json, then re-run.")


if __name__ == "__main__":
    main()
