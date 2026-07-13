"""Stage: script-review — critique the narration, then revise flagged scenes.

A narration quality agent (text-only, no credits). It reads the generated
narration and flags scenes that are weak, so they can be rewritten before TTS:

  - hook:    scene 1 must open on a provocative question that makes the viewer
             need to know — NOT the verdict, NOT "in this video" throat-clearing.
  - verdict: the whole thing must take a real point of view, not summarize.
  - filler:  YouTube clichés ("let's dive in", "hey guys"), filler ("basically",
             "to be honest", "at the end of the day"), engagement-bait CTAs.
  - vague:   hand-wavy claims with no concrete example or specific bite.
  - spoken:  natural to hear aloud; not too long/dense for one scene.

`script_review()` writes `scene["narration_review"] = {ok, issues}`.
`revise_narration()` rewrites the flagged scenes' narration in one pass (using the
critique + full-script context so the arc stays coherent) with the stronger `script`
model, and clears the stale reviews.
"""

from __future__ import annotations

import json
from typing import Any

from .config import load_config, resolve_path
from .llm import call_stage

_REVIEW_SYSTEM = (
    "You are a sharp script editor for honest, long-form book-verdict videos. You "
    "catch weak hooks, filler, clichés, vague claims, and summary-instead-of-stance, "
    "and you are specific. You return only valid JSON."
)
_REVISE_SYSTEM = (
    "You are a sharp, honest video essayist. You rewrite narration to fix specific "
    "notes while keeping the scene's role in the arc and a natural spoken voice. You "
    "return only valid JSON."
)


def _scenes_block(scenes: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"Scene {s['id']}:\n{s.get('narration') or s.get('narration_en', '')}"
        for s in scenes
    )


def _review_prompt(scenes: list[dict[str, Any]]) -> str:
    return (
        "Review the narration for each scene of this long-form book-verdict video. "
        "Scene 1 is the intro and must open on a PROVOCATIVE QUESTION that makes the "
        "viewer feel it personally — not the verdict, not 'in this video' / 'my honest "
        "verdict' throat-clearing. The video overall must take a real POINT OF VIEW, "
        "not summarize.\n\n"
        "For EACH scene, flag genuine problems (not nitpicks):\n"
        "- weak or missing hook (especially scene 1),\n"
        "- YouTube clichés ('let's dive in', 'hey guys', 'without further ado'), filler "
        "('basically', 'to be honest', 'at the end of the day', 'sort of'), or "
        "engagement-bait CTAs ('like and subscribe'),\n"
        "- vague, hand-wavy claims with no concrete example or specific bite,\n"
        "- summarizing instead of taking a stance,\n"
        "- narration too long/dense or awkward to say aloud.\n\n"
        f"{_scenes_block(scenes)}\n\n"
        'Return JSON: {"scenes": [{"id": <int>, "ok": <bool>, "issues": ["short, '
        'specific problem", ...]}, ...]} for EVERY scene id. ok = true only when the '
        "narration is genuinely strong; then issues must be []. ok = false with a short, "
        "specific issue for each real problem (what is wrong and how to sharpen it)."
    )


def _combined_issues(s: dict[str, Any]) -> list[str]:
    """A scene's open review notes from BOTH the narration critic and the fact-check
    agent (fact notes tagged so `revise` grounds them in the book)."""
    issues: list[str] = []
    nr = s.get("narration_review")
    if isinstance(nr, dict) and not nr.get("ok"):
        issues += list(nr.get("issues", []))
    fr = s.get("fact_review")
    if isinstance(fr, dict) and not fr.get("ok"):
        issues += [f"[fact] {i}" for i in fr.get("issues", [])]
    return issues


def _revise_prompt(
    scenes: list[dict[str, Any]], targets: list[dict[str, Any]], book: str | None = None
) -> str:
    notes = "\n\n".join(
        f"Scene {t['id']} — fix these: "
        + ("; ".join(t["issues"]) if t["issues"] else "sharpen and tighten")
        for t in targets
    )
    ids = [t["id"] for t in targets]
    book_block = ""
    if book:
        book_block = (
            "\n\nBOOK TEXT — ground any claim in THIS. For notes tagged [fact], fix them "
            "by matching what the book actually says or by reframing the claim as your own "
            "take / 'widely reported'; never invent quotes, stats, or details:\n"
            f"<<<BOOK\n{book}\nBOOK\n"
        )
    return (
        "Here is the full narration for a long-form book-verdict video, for context "
        "(keep the overall arc and continuity intact):\n\n"
        f"{_scenes_block(scenes)}"
        f"{book_block}\n\n"
        f"Rewrite ONLY these scenes to fix the notes, keeping each scene's role in the "
        f"arc, first person, natural spoken narration (about 2-5 sentences). Scene 1, if "
        f"listed, must open on a provocative question — never the verdict.\n\n{notes}\n\n"
        f'Return JSON: {{"scenes": [{{"id": <int>, "narration": "..."}}, ...]}} '
        f"containing exactly these scene ids: {ids}."
    )


def _validate_review(data: dict[str, Any], ids: set[int]) -> dict[int, dict[str, Any]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("script-review: model returned no scenes")
    out: dict[int, dict[str, Any]] = {}
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"script-review: entry #{i} is not an object")
        try:
            sid = int(s.get("id"))
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"script-review: entry #{i} has no valid id") from e
        raw = s.get("issues") or []
        if not isinstance(raw, list):
            raw = [str(raw)]
        issues = [str(x).strip() for x in raw if str(x).strip()]
        out[sid] = {"ok": bool(s.get("ok")) and not issues, "issues": issues}
    missing = ids - set(out)
    if missing:
        raise RuntimeError(f"script-review: model skipped scenes {sorted(missing)}")
    return out


def script_review(*, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Critique every scene's narration; write narration_review back into scenes.json.

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

    print(f"[script-review] reviewing narration for {len(scenes)} scenes (no credits) ...")
    data = call_stage(
        cfg, "script_review", _review_prompt(scenes),
        system=_REVIEW_SYSTEM, json_out=True,
    )
    by_id = _validate_review(data, {int(s["id"]) for s in scenes})

    flagged = []
    for s in scenes:
        r = by_id[int(s["id"])]
        s["narration_review"] = r
        if not r["ok"]:
            flagged.append(s["id"])

    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    n_ok = len(scenes) - len(flagged)
    if flagged:
        print(f"[script-review] {n_ok}/{len(scenes)} scenes strong. Flagged {flagged}:")
        for s in scenes:
            r = s.get("narration_review") or {}
            if not r.get("ok"):
                for issue in r.get("issues", []):
                    print(f"  scene {s['id']:>2}: {issue}")
        print("[script-review] fix with `revise` (rewrites flagged scenes) or edit by hand.")
    else:
        print(f"[script-review] all {len(scenes)} scenes read strong.")
    return {"n_ok": n_ok, "n_scenes": len(scenes), "flagged": flagged}


def revise_narration(
    scene_ids: list[int] | None = None, *, cfg: dict[str, Any] | None = None
) -> list[int]:
    """Rewrite the narration of flagged scenes (or scene_ids) to fix their review
    notes, in one context-aware pass. Returns the list of revised scene ids."""
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    by_id = {int(s["id"]): s for s in scenes}
    if scene_ids is None:
        targets = [
            {"id": s["id"], "issues": _combined_issues(s)}
            for s in scenes if _combined_issues(s)
        ]
    else:
        targets = [
            {"id": int(i), "issues": _combined_issues(by_id[int(i)])}
            for i in scene_ids if int(i) in by_id
        ]
    if not targets:
        print("[revise] nothing flagged — run `script-review` or `fact-check` first "
              "(or pass scene ids).")
        return []

    # If any target has a fact-grounding issue, give the rewriter the book to fix against.
    has_fact = any(
        isinstance(by_id[t["id"]].get("fact_review"), dict)
        and not by_id[t["id"]]["fact_review"].get("ok")
        for t in targets
    )
    book = None
    if has_fact:
        try:
            from .fact_review import load_book_excerpt
            book = load_book_excerpt(cfg, 80_000)
        except FileNotFoundError:
            book = None  # no book (e.g. synthetic project) — revise notes without it

    print(f"[revise] rewriting narration for scenes {[t['id'] for t in targets]}"
          + (" (grounded in the book)" if book else "") + " ...")
    data = call_stage(
        cfg, "script", _revise_prompt(scenes, targets, book),
        system=_REVISE_SYSTEM, json_out=True,
    )
    revised = data.get("scenes")
    if not isinstance(revised, list) or not revised:
        raise RuntimeError("revise: model returned no scenes")

    changed = []
    for r in revised:
        if not isinstance(r, dict):
            continue
        try:
            sid = int(r.get("id"))
        except (TypeError, ValueError):
            continue
        text = str(r.get("narration") or "").strip()
        if sid in by_id and text:
            by_id[sid]["narration"] = text
            # rewritten — both reviews are stale and must be re-run
            by_id[sid]["narration_review"] = None
            by_id[sid]["fact_review"] = None
            changed.append(sid)

    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[revise] rewrote {len(changed)} scenes {changed}. Re-run `script-review`, "
          "then re-narrate those scenes.")
    return changed


def narration_review_gate(scenes: list[dict[str, Any]]) -> list[int]:
    """Scene ids that have been reviewed and are flagged (for a soft UI warning)."""
    return [
        s["id"] for s in scenes
        if isinstance(s.get("narration_review"), dict) and not s["narration_review"].get("ok")
    ]
