"""Stage: review — validate the visual prompts BEFORE spending any credits.

Text-only, ZERO image/clip credits. This is the safety net between `visuals`
(which writes prompts) and `images`/animate (which cost money). For each scene the
model judges:
  - relevance:  does start_image_prompt actually depict this scene's narration?
  - coherence:  is end_image_prompt the same scene a moment later (a plausible end
                frame of a subtle motion), not a different/unrelated image?
  - motion:     does video_prompt describe a gentle start->end motion for the pair?

It writes `scene["review"] = {"ok": bool, "issues": [str, ...]}` back into
scenes.json. `images` refuses to generate while any scene is unreviewed or failing
(override with --skip-review), so bad prompts get caught for free.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_config, resolve_path
from .llm import call_stage

_SYSTEM = (
    "You are a meticulous art-direction reviewer. You catch prompts that do not "
    "match the narration or that would not animate as a coherent pair, and you are "
    "specific about why. You return only valid JSON."
)


def _build_prompt(scenes: list[dict[str, Any]]) -> str:
    blocks = []
    for s in scenes:
        animated = bool(s.get("animate"))
        kind = f"ANIMATED ({s.get('mode', 'MOTION')})" if animated else "STILL (Ken Burns pan)"
        block = (
            f"Scene {s['id']} — {kind}:\n"
            f"  narration: {s.get('narration') or s.get('narration_en', '')}\n"
            f"  start_image_prompt: {s.get('start_image_prompt', '')}"
        )
        if animated:
            block += (
                f"\n  end_image_prompt: {s.get('end_image_prompt', '')}\n"
                f"  video_prompt: {s.get('video_prompt', '')}"
            )
        blocks.append(block)
    scenes_block = "\n\n".join(blocks)
    return (
        f"The art style is LOW-POLY 3D — stylized, faceted characters WITH clear faces are "
        f"correct and good; only flag PHOTOREALISTIC faces/hands, never low-poly ones.\n\n"
        f"Most scenes are STILL (a single Ken Burns pan over one image) — they have NO "
        f"end_image_prompt or video_prompt ON PURPOSE. Do NOT flag a still scene for missing "
        f"motion, missing end frame, or empty video_prompt. Only ANIMATED scenes get the "
        f"motion/coherence checks.\n\n"
        f"Review each scene below:\n"
        f"1. Relevance (ALL scenes) — does start_image_prompt depict what this scene's "
        f"narration is about? Flag it if off-topic or generic filler.\n"
        f"2. Coherence (ANIMATED scenes only) — is end_image_prompt the SAME scene a moment "
        f"later (same setting/subject, one subtle change)? Flag if it is unrelated.\n"
        f"3. Motion (ANIMATED scenes only) — does video_prompt describe a subtle, slow "
        f"start->end camera move (no shake, no NEW characters)? Flag if not.\n\n"
        f"{scenes_block}\n\n"
        f'Return JSON: {{"scenes": [{{"id": <int>, "ok": <bool>, '
        f'"issues": ["short, specific problem", ...]}}, ...]}} for EVERY scene id.\n'
        f"- ok = true when the applicable checks pass (relevance for stills; relevance + "
        f"coherence + motion for animated). When ok = true, issues must be [].\n"
        f"- ok = false only for a GENUINE problem that would hurt the video; list each as a "
        f"short, specific string. Do NOT invent nitpicks, and do NOT flag stills for lacking "
        f"motion."
    )


def _validate(data: dict[str, Any], ids: set[int]) -> dict[int, dict[str, Any]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("review: model returned no scenes")
    out: dict[int, dict[str, Any]] = {}
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"review: entry #{i} is not an object")
        try:
            sid = int(s.get("id"))
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"review: entry #{i} has no valid id") from e
        raw_issues = s.get("issues") or []
        if not isinstance(raw_issues, list):
            raw_issues = [str(raw_issues)]
        issues = [str(x).strip() for x in raw_issues if str(x).strip()]
        ok = bool(s.get("ok")) and not issues
        out[sid] = {"ok": ok, "issues": issues}
    missing = ids - set(out)
    if missing:
        raise RuntimeError(f"review: model skipped scenes {sorted(missing)}")
    return out


def review(*, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate every scene's visual prompts; write review back into scenes.json.

    Returns a summary: {"passed": bool, "n_ok": int, "n_scenes": int, "failing": [ids]}.
    """
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    unprompted = [s["id"] for s in scenes if not (s.get("start_image_prompt") or "").strip()]
    if unprompted:
        raise RuntimeError(
            f"review: scenes {unprompted} have no visual prompts yet — run `visuals` first."
        )

    print(f"[review] validating {len(scenes)} scenes (text-only, no credits) ...")
    data = call_stage(
        cfg, "review", _build_prompt(scenes), system=_SYSTEM, json_out=True
    )
    by_id = _validate(data, {int(s["id"]) for s in scenes})

    failing = []
    for s in scenes:
        r = by_id[int(s["id"])]
        s["review"] = r
        if not r["ok"]:
            failing.append(s["id"])

    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    n_ok = len(scenes) - len(failing)
    summary = {
        "passed": not failing,
        "n_ok": n_ok,
        "n_scenes": len(scenes),
        "failing": failing,
    }
    if failing:
        print(f"[review] {n_ok}/{len(scenes)} scenes OK. Issues in scenes {failing}:")
        for s in scenes:
            r = s.get("review") or {}
            if not r.get("ok"):
                for issue in r.get("issues", []):
                    print(f"  scene {s['id']:>2}: {issue}")
        print("[review] fix the prompts (edit + re-run `visuals`/`review`), or generate "
              "anyway with --skip-review.")
    else:
        print(f"[review] all {len(scenes)} scenes passed. Safe to run `images`.")
    return summary


def review_gate(scenes: list[dict[str, Any]]) -> tuple[list[int], list[int]]:
    """For the images/animate gate: (unreviewed ids, failing ids) among scenes that
    actually have visual prompts. Empty/empty means it is safe to generate."""
    unreviewed, failing = [], []
    for s in scenes:
        if not (s.get("start_image_prompt") or "").strip():
            continue  # legacy scene without visuals — not gated
        r = s.get("review")
        if not isinstance(r, dict):
            unreviewed.append(s["id"])
        elif not r.get("ok"):
            failing.append(s["id"])
    return unreviewed, failing
