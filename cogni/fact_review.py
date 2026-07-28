"""Stage: fact-check — ground the narration in the actual book (no credits).

The `script` stage writes from the outline plus the model's own knowledge, so the
narration can drift: state things the book never says, contradict it, or slip an
outside claim in as if it were the book's. For an honest-verdict channel that's a
credibility risk. This agent reads the real `book.md` and each scene's narration and
flags, per scene:

  - contradiction: a claim that conflicts with what the book actually says,
  - not-in-book:   a claim presented as the book's content that isn't in the book
                   (a likely fabrication — invented quote, stat, or detail),
  - unlabeled-opinion: outside-the-book commentary stated as fact rather than framed
                   as the narrator's take.

A stance/verdict is fine — the channel is opinion, not summary — so honest commentary
that's clearly the narrator's view is NOT flagged. It writes
`scene["fact_review"] = {ok, issues}`; the `revise` step (script_review) can then
rewrite flagged scenes with the book in context.

TREAT THE OUTPUT AS A LEAD, NOT A VERDICT. Measured on book #5: two runs over the same
script and the same (deterministic) excerpt returned 3 flags and then 0 — the variance
is the model. So a clean pass is NOT proof of a clean script, and a flag is not proof
of a problem: all 3 of those flags were false, and the quote they called fabricated is
verbatim in the book. `verify_not_in_book` now clears that specific failure mode
automatically, but nothing here can recover a fabrication the model didn't notice.
Run it, read the flags, and check the surprising ones against the book yourself.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .config import load_config, resolve_path
from .ingest import _budget_text
from .llm import call_stage

# How many scenes to check per call. The book excerpt is resent with each batch, so
# bigger batches are cheaper — but one call carrying 94 scenes plus 160k of book is the
# shape that blew the CLI timeout on an 81-scene visuals pass.
_SCENES_PER_CALL = 20

# The book can be large; cap what we send. Opus has a big context, but this keeps the
# call sane and fast. Long books are truncated (logged) — fact-check what fits.
_MAX_BOOK_CHARS = 160_000

_SYSTEM = (
    "You are a rigorous fact-checker for a book-commentary video. You compare a script "
    "against the actual book text and flag only genuine grounding problems — never "
    "style. You return only valid JSON."
)


def load_book_excerpt(cfg: dict[str, Any], max_chars: int = _MAX_BOOK_CHARS) -> str:
    """The book text for grounding, sampled evenly across the WHOLE book.

    This used to take `text[:max_chars]` — the first 160k of a 306k book, i.e. barely
    half. Everything the script drew from the back half then looked absent, so a true
    claim about the ending would be flagged "not-in-book" while a fabrication about it
    sailed through unchecked. Sampling evenly (the same helper `ingest` uses to read a
    long book) means every part of the book is represented in the excerpt.
    """
    book_path = resolve_path(cfg, "book_md")
    if not book_path.exists():
        raise FileNotFoundError(
            f"{book_path} not found — run `convert` first so fact-check has the book."
        )
    text = book_path.read_text(encoding="utf-8").strip()
    excerpt, sampled = _budget_text(text, max_chars)
    if sampled:
        print(f"[fact-check] book is {len(text)} chars; sampling {max_chars} evenly "
              "across the whole book (gaps are marked [...]).")
    return excerpt


def _build_prompt(book: str, scenes: list[dict[str, Any]]) -> str:
    blocks = "\n\n".join(
        f"Scene {s['id']}:\n{s.get('narration') or s.get('narration_en', '')}"
        for s in scenes
    )
    return (
        "BOOK TEXT (the source of truth — only this counts as 'the book'):\n"
        "<<<BOOK\n"
        f"{book}\n"
        "BOOK\n\n"
        "SCRIPT SCENES (the narration to check):\n"
        f"{blocks}\n\n"
        "For EACH scene, check its factual claims against the BOOK TEXT and flag only "
        "genuine grounding problems:\n"
        "- contradiction: the narration conflicts with what the book actually says.\n"
        "- not-in-book: the narration presents something as the book's content "
        "(an idea, quote, statistic, or detail) that is NOT in the book text — a likely "
        "fabrication.\n"
        "- unlabeled-opinion: an outside-the-book claim (real-world context, author "
        "biography, controversy) stated as flat fact instead of clearly framed as the "
        "narrator's own take or 'widely reported'.\n\n"
        "IMPORTANT: this is an opinion/verdict video, so a clear stance or honest "
        "commentary is FINE and must NOT be flagged — only flag claims that contradict "
        "the book, are falsely attributed to the book, or are outside facts dressed up "
        "as certainty. If the book excerpt is too short to judge a claim, do not guess.\n\n"
        'Return JSON: {"scenes": [{"id": <int>, "ok": <bool>, "issues": ["<type>: '
        'short specific problem and the fix", ...]}, ...]} for EVERY scene id. ok = true '
        "when the scene has no grounding problem (issues = []); ok = false with a short, "
        "specific issue for each real problem (name the type, quote the claim, say what "
        "the book actually supports)."
    )


_QUOTE_RE = re.compile(r"['‘’\"“”]([^'‘’\"“”]{12,240})['‘’\"“”]")


def _norm(s: str) -> str:
    """Fold the differences that make a real quote look absent: curly quotes, dashes,
    case and whitespace. The book uses em-dashes and smart quotes; scripts don't."""
    s = s.lower()
    s = re.sub(r"[‘’“”]", "'", s)
    s = re.sub(r"[‐-―−]", "-", s)
    return re.sub(r"\s+", " ", s).strip()


def verify_not_in_book(issue: str, full_book_norm: str) -> bool:
    """True if this 'not-in-book' issue is a FALSE POSITIVE — i.e. the claim it quotes
    really is in the book.

    Why this exists: the excerpt sent to the model is sampled (160k of a 299k book), so
    a line that appears exactly ONCE can land in a gap. That happened — the model
    flagged Frankl's "the best of us did not return" across three beats as fabricated,
    with a confident rationale, when it is verbatim in the text. Sampling can prove
    presence, never absence, so absence is re-checked against the FULL book.

    Only the FIRST quoted span is checked: that's the flagged claim. Later spans are
    usually the correction ("the book actually says ..."), which IS in the book — using
    those would delete every true flag.
    """
    if "not-in-book" not in issue.lower():
        return False
    m = _QUOTE_RE.search(issue)
    if not m:
        return False
    claim = _norm(m.group(1))
    return len(claim.split()) >= 4 and claim in full_book_norm


def _validate(data: dict[str, Any], ids: set[int]) -> dict[int, dict[str, Any]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("fact-check: model returned no scenes")
    out: dict[int, dict[str, Any]] = {}
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"fact-check: entry #{i} is not an object")
        try:
            sid = int(s.get("id"))
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"fact-check: entry #{i} has no valid id") from e
        raw = s.get("issues") or []
        if not isinstance(raw, list):
            raw = [str(raw)]
        issues = [str(x).strip() for x in raw if str(x).strip()]
        out[sid] = {"ok": bool(s.get("ok")) and not issues, "issues": issues}
    missing = ids - set(out)
    if missing:
        raise RuntimeError(f"fact-check: model skipped scenes {sorted(missing)}")
    return out


def fact_review(*, force: bool = False, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Check narration against book.md; write fact_review back into scenes.json.

    Converges like script-review: only scenes not yet fact-checked (fact_review is
    None) are (re)checked; already-cleared scenes keep their verdict. force=True
    rechecks all. The model always sees the full script for context.
    Returns {"n_ok", "n_scenes", "flagged", "checked"}.
    """
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    targets = scenes if force else [
        s for s in scenes if not isinstance(s.get("fact_review"), dict)
    ]
    checked = [s["id"] for s in targets]
    if targets:
        book = load_book_excerpt(cfg)
        # The FULL text (not the sampled excerpt) is what clears false "not-in-book"
        # flags — sampling can prove a line is present, never that it is absent.
        full_norm = _norm(resolve_path(cfg, "book_md").read_text(encoding="utf-8"))
        print(f"[fact-check] grounding {len(targets)} scene(s) against the book (no credits) ...")
        # Batched: one call per _SCENES_PER_CALL scenes. Each batch is checked against
        # the same book excerpt, and results are written back after EVERY batch — so a
        # failure late in a long book keeps the work already done instead of losing it.
        for i in range(0, len(targets), _SCENES_PER_CALL):
            batch = targets[i : i + _SCENES_PER_CALL]
            ids = {int(s["id"]) for s in batch}
            print(f"[fact-check]   scenes {min(ids)}-{max(ids)} "
                  f"({i // _SCENES_PER_CALL + 1}/{(len(targets) - 1) // _SCENES_PER_CALL + 1}) ...")
            data = call_stage(
                cfg, "fact_review", _build_prompt(book, batch), system=_SYSTEM, json_out=True
            )
            by_id = _validate(data, ids)
            for s in batch:
                r = by_id[int(s["id"])]
                kept, cleared = [], []
                for issue in r["issues"]:
                    (cleared if verify_not_in_book(issue, full_norm) else kept).append(issue)
                for c in cleared:
                    # Loudly: a silently-dropped flag is indistinguishable from a gate
                    # that isn't running.
                    print(f"[fact-check]   scene {s['id']}: cleared a false 'not-in-book' "
                          f"— the quoted line IS in the full book ({c[:80]}...)")
                s["fact_review"] = {"ok": not kept, "issues": kept}
            scenes_path.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    else:
        print("[fact-check] nothing new to check — every scene already grounded "
              "(revise or edit a scene to re-check it, or use force to redo all).")

    flagged = [s["id"] for s in scenes
               if isinstance(s.get("fact_review"), dict) and not s["fact_review"]["ok"]]
    n_ok = sum(1 for s in scenes if isinstance(s.get("fact_review"), dict) and s["fact_review"]["ok"])
    if flagged:
        print(f"[fact-check] {n_ok}/{len(scenes)} clean. Grounding issues in {flagged}:")
        for s in scenes:
            r = s.get("fact_review") or {}
            if isinstance(s.get("fact_review"), dict) and not r.get("ok"):
                for issue in r.get("issues", []):
                    print(f"  scene {s['id']:>2}: {issue}")
        print("[fact-check] fix with `revise` (grounds the rewrite in the book) or edit by hand.")
    else:
        print(f"[fact-check] all {len(scenes)} scenes are grounded in the book.")
    return {"n_ok": n_ok, "n_scenes": len(scenes), "flagged": flagged, "checked": checked}


def fact_review_gate(scenes: list[dict[str, Any]]) -> list[int]:
    """Scene ids that have been fact-checked and are flagged (for a soft UI warning)."""
    return [
        s["id"] for s in scenes
        if isinstance(s.get("fact_review"), dict) and not s["fact_review"].get("ok")
    ]
