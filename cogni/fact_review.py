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
"""

from __future__ import annotations

import json
from typing import Any

from .config import load_config, resolve_path
from .llm import call_stage

# The book can be large; cap what we send. Opus has a big context, but this keeps the
# call sane and fast. Long books are truncated (logged) — fact-check what fits.
_MAX_BOOK_CHARS = 160_000

_SYSTEM = (
    "You are a rigorous fact-checker for a book-commentary video. You compare a script "
    "against the actual book text and flag only genuine grounding problems — never "
    "style. You return only valid JSON."
)


def load_book_excerpt(cfg: dict[str, Any], max_chars: int = _MAX_BOOK_CHARS) -> str:
    """The book text for grounding, capped to max_chars (truncation logged)."""
    book_path = resolve_path(cfg, "book_md")
    if not book_path.exists():
        raise FileNotFoundError(
            f"{book_path} not found — run `convert` first so fact-check has the book."
        )
    text = book_path.read_text(encoding="utf-8").strip()
    if len(text) > max_chars:
        print(f"[fact-check] book is {len(text)} chars; using the first {max_chars} "
              "(fact-check only covers what fits).")
        text = text[:max_chars]
    return text


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


def fact_review(*, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Check every scene's narration against book.md; write fact_review to scenes.json.

    Returns {"n_ok": int, "n_scenes": int, "flagged": [ids]}.
    """
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    book = load_book_excerpt(cfg)
    print(f"[fact-check] grounding {len(scenes)} scenes against the book (no credits) ...")
    data = call_stage(
        cfg, "fact_review", _build_prompt(book, scenes), system=_SYSTEM, json_out=True
    )
    by_id = _validate(data, {int(s["id"]) for s in scenes})

    flagged = []
    for s in scenes:
        r = by_id[int(s["id"])]
        s["fact_review"] = r
        if not r["ok"]:
            flagged.append(s["id"])

    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    n_ok = len(scenes) - len(flagged)
    if flagged:
        print(f"[fact-check] {n_ok}/{len(scenes)} scenes clean. Grounding issues in {flagged}:")
        for s in scenes:
            r = s.get("fact_review") or {}
            if not r.get("ok"):
                for issue in r.get("issues", []):
                    print(f"  scene {s['id']:>2}: {issue}")
        print("[fact-check] fix with `revise` (grounds the rewrite in the book) or edit by hand.")
    else:
        print(f"[fact-check] all {len(scenes)} scenes are grounded in the book.")
    return {"n_ok": n_ok, "n_scenes": len(scenes), "flagged": flagged}


def fact_review_gate(scenes: list[dict[str, Any]]) -> list[int]:
    """Scene ids that have been fact-checked and are flagged (for a soft UI warning)."""
    return [
        s["id"] for s in scenes
        if isinstance(s.get("fact_review"), dict) and not s["fact_review"].get("ok")
    ]
