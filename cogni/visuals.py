"""Stage: visuals — scenes.json narration -> per-scene keyframe + motion prompts.

Creative, text-only, ZERO image/clip credits. For each scene the model writes:
  - start_image_prompt: the opening still (concrete subject + composition)
  - end_image_prompt:   kept for the schema/UI; the animate step no longer interpolates
                        to it (see docs/motion.md — near-identical frames froze the clips)
  - video_prompt:       ONE real, slow camera move (push-in, pan, parallax, ...) that
                        the animate step applies to the start still — describes only the
                        move, not what's already in the image

These feed downstream stages: `images` renders start_image_prompt as the still, and the
animate step (cogni-animate skill) drives a Seedance clip from that single still using
video_prompt. See docs/motion.md for the camera-move vocabulary.
The art STYLE token is appended at image-generation time, so prompts stay
style-agnostic here (subject/composition only), exactly like `script`'s seed prompt.

Cached: scenes that already have prompts are left alone unless --force.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_config, resolve_path
from .llm import call_stage

_SYSTEM = (
    "You are an art director writing image and motion prompts for a calm, "
    "contemplative long-form video. You return only valid JSON."
)


def _build_prompt(scenes: list[dict[str, Any]], title: str, thesis: str) -> str:
    blocks = []
    for s in scenes:
        seed = (s.get("image_prompt") or "").strip()
        blocks.append(
            f"Scene {s['id']}:\n"
            f"  narration: {s.get('narration') or s.get('narration_en', '')}\n"
            + (f"  seed image idea: {seed}\n" if seed else "")
        )
    scenes_block = "\n".join(blocks)
    return (
        f"Video: {title}\nThesis: {thesis}\n\n"
        f"For EACH scene below, write three things that visually carry the narration:\n"
        f"{scenes_block}\n"
        f'Return JSON: {{"scenes": [{{"id": <int>, "start_image_prompt": ..., '
        f'"end_image_prompt": ..., "video_prompt": ...}}, ...]}} covering every scene id.\n'
        f"- start_image_prompt: ONE still that opens the scene — concrete subject and "
        f"composition that fits the narration. No realistic human faces or hands; favor "
        f"landscapes, silhouettes, objects, symbolic imagery, or figures seen from behind "
        f"or far away. Do NOT mention art style (added later).\n"
        f"- end_image_prompt: the SAME scene a moment later — the identical setting and "
        f"subject with ONE subtle change (light shifts, a slow drift, one element moves). "
        f"It must read as the end frame of a gentle motion from start_image_prompt, NOT a "
        f"new or unrelated image. Same constraints (no faces/hands, no style).\n"
        f"- video_prompt: ONE deliberate, slow CAMERA MOVE that serves the narration, named "
        f"in cinematographer's terms — slow push-in / dolly-in, slow pull-back / dolly-out, "
        f"pan left or right, tilt up or down, lateral tracking, slow orbit, or parallax. "
        f"Describe ONLY the camera move (plus at most one thing that shifts, e.g. light "
        f"warming); do NOT re-describe what is already in the still — that dampens the "
        f"motion. Calm and slow, never frantic, no new characters or faces. BANNED phrasing "
        f"(it freezes the model): 'no camera shake', 'static', 'still', 'gentle drift', "
        f"'barely perceptible', 'remains'. Pick one real move."
    )


def _validate(data: dict[str, Any], ids: set[int]) -> dict[int, dict[str, str]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("visuals: model returned no scenes")
    out: dict[int, dict[str, str]] = {}
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"visuals: entry #{i} is not an object")
        try:
            sid = int(s.get("id"))
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"visuals: entry #{i} has no valid id") from e
        start = str(s.get("start_image_prompt") or "").strip()
        end = str(s.get("end_image_prompt") or "").strip()
        motion = str(s.get("video_prompt") or "").strip()
        if not (start and end and motion):
            raise RuntimeError(
                f"visuals: scene {sid} is missing start/end/video prompt"
            )
        out[sid] = {
            "start_image_prompt": start,
            "end_image_prompt": end,
            "video_prompt": motion,
        }
    missing = ids - set(out)
    if missing:
        raise RuntimeError(f"visuals: model skipped scenes {sorted(missing)}")
    return out


def visuals(*, force: bool = False, cfg: dict[str, Any] | None = None) -> Path:
    """Write start/end/video prompts for every scene in scenes.json (cached)."""
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    have_all = all((s.get("start_image_prompt") or "").strip() for s in scenes)
    if have_all and not force:
        print(f"[visuals] cached — all {len(scenes)} scenes have prompts (use --force).")
        return scenes_path

    print(f"[visuals] writing keyframe + motion prompts for {len(scenes)} scenes ...")
    data = call_stage(
        cfg,
        "visuals",
        _build_prompt(scenes, doc.get("project_title", ""), doc.get("thesis", "")),
        system=_SYSTEM,
        json_out=True,
    )
    by_id = _validate(data, {int(s["id"]) for s in scenes})

    for s in scenes:
        v = by_id[int(s["id"])]
        s["start_image_prompt"] = v["start_image_prompt"]
        s["end_image_prompt"] = v["end_image_prompt"]
        s["video_prompt"] = v["video_prompt"]
        s["review"] = None   # prompts changed — any prior review is stale

    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[visuals] wrote prompts for {len(scenes)} scenes. Next: `review`.")
    return scenes_path
