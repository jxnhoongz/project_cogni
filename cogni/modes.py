"""Stage: modes — decide which beats earn motion, and describe that motion.

Text-only, ZERO image/clip credits. Every scene is tagged with a motion MODE and,
for the animated ones, a `video_prompt` describing only the camera/element move:

  - LOW    = a still with a very slow Ken Burns pan/zoom. FREE, and it fits most beats.
  - MEDIUM = one subtle element in motion, or a gentle push-in. Costs Higgsfield credits.
  - HIGH   = full lively motion (a bigger camera move + element motion), reserved for the
             biggest emotional / reveal / impact beats. Costs the most.

Motion costs money, so the model is told to be selective (see config `modes.max_animated`).
Beat 1 (the cold open) is ALWAYS forced to HIGH — it has to hook. For each MEDIUM/HIGH
beat we write `scene["video_prompt"]`; LOW beats get "". `scene["animate"]` is set to
True for MEDIUM/HIGH so the downstream Higgsfield step knows which beats to render.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .config import load_config, resolve_path
from .llm import call_stage

_SYSTEM = (
    "You are the motion director for a long-form explainer video. You decide which "
    "beats earn on-screen motion and describe that motion precisely. You return only "
    "valid JSON."
)

_VALID_MODES = ("LOW", "MEDIUM", "HIGH")
_ANIMATED = ("MEDIUM", "HIGH")
_FALLBACK_PROMPT = "Very slow push-in."


def _build_prompt(doc: dict[str, Any], max_animated: int) -> str:
    lines = []
    for s in doc.get("scenes", []):
        chapter = str(s.get("chapter") or "-")
        narration = str(s.get("narration") or "").strip()
        line = f"Beat {s['id']} [{chapter}]: {narration}"
        ost = str(s.get("on_screen_text") or "").strip()
        if ost:
            line += f" (on-screen: {ost})"
        lines.append(line)
    beats_block = "\n".join(lines)
    return (
        f"Project: {doc.get('project_title', '')}\n"
        f"Thesis: {doc.get('thesis', '')}\n\n"
        f"Here are all the beats of the video, in order:\n"
        f"{beats_block}\n\n"
        f"Assign every beat one of three motion MODES:\n"
        f"- LOW = a still with a very slow Ken Burns pan/zoom. FREE, and it fits MOST beats.\n"
        f"- MEDIUM = one subtle element in motion, or a gentle push-in. Costs credits.\n"
        f"- HIGH = full lively motion: a bigger camera move PLUS element motion, reserved "
        f"for the biggest emotional / reveal / impact beats. Costs the most.\n\n"
        f"Rules:\n"
        f"- Beat 1 (the cold open) MUST be HIGH — it has to hook the viewer.\n"
        f"- The final verdict beat and 1-2 chapter-peak / reveal beats are strong HIGH "
        f"candidates.\n"
        f"- Motion costs money, so be selective: across the WHOLE video pick AT MOST about "
        f"{max_animated} beats total for MEDIUM or HIGH combined; every other beat is LOW.\n"
        f"- For each MEDIUM or HIGH beat, write a `video_prompt` describing ONLY the motion: "
        f"a real slow camera move (push-in / pull-back / pan / tilt / parallax) and/or ONE "
        f"element that moves. Present tense, one primary move. Do NOT re-describe the static "
        f'image. Banned words: "static", "no motion", "still", "gentle drift". '
        f'LOW beats get "".\n\n'
        f'Return JSON: {{"scenes": [{{"id": <int>, "mode": "LOW"|"MEDIUM"|"HIGH", '
        f'"video_prompt": <string>}}, ...]}} for EVERY beat id.'
    )


def _validate(data: dict[str, Any], ids: Iterable[int]) -> dict[int, dict[str, Any]]:
    """Normalize the model's tags into {id: {"mode", "video_prompt"}} for every id.

    - Coerces any unknown mode to LOW.
    - Missing ids default to LOW (motion is opt-in, LOW is free and safe).
    - FORCES beat id==1 to HIGH regardless of what the model returned.
    - A MEDIUM/HIGH beat with an empty video_prompt falls back to a slow push-in;
      LOW beats always get "".
    """
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("modes: model returned no scenes")

    by_id: dict[int, dict[str, Any]] = {}
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"modes: entry #{i} is not an object")
        try:
            sid = int(s.get("id"))
        except (TypeError, ValueError) as e:
            raise RuntimeError(f"modes: entry #{i} has no valid id") from e
        mode = str(s.get("mode") or "").strip().upper()
        if mode not in _VALID_MODES:
            mode = "LOW"
        by_id[sid] = {
            "mode": mode,
            "video_prompt": str(s.get("video_prompt") or "").strip(),
        }

    out: dict[int, dict[str, Any]] = {}
    for sid in ids:
        entry = by_id.get(sid, {"mode": "LOW", "video_prompt": ""})
        mode = entry["mode"]
        video_prompt = entry["video_prompt"]
        if sid == 1:
            mode = "HIGH"  # cold open always earns motion
        if mode in _ANIMATED:
            video_prompt = video_prompt or _FALLBACK_PROMPT
        else:
            video_prompt = ""
        out[sid] = {"mode": mode, "video_prompt": video_prompt}
    return out


def modes(*, force: bool = False, cfg: dict[str, Any] | None = None) -> Path:
    """Tag every scene LOW/MEDIUM/HIGH and write motion prompts back into scenes.json."""
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    if not force and all(s.get("mode") is not None for s in scenes):
        print("[modes] cached")
        return scenes_path

    max_animated = int(cfg.get("modes", {}).get("max_animated", 12))

    print(f"[modes] tagging {len(scenes)} beats LOW/MEDIUM/HIGH (text-only, no credits) ...")
    data = call_stage(cfg, "modes", _build_prompt(doc, max_animated), system=_SYSTEM, json_out=True)
    by_id = _validate(data, {int(s["id"]) for s in scenes})

    for s in scenes:
        r = by_id[int(s["id"])]
        s["mode"] = r["mode"]
        s["video_prompt"] = r["video_prompt"]
        s["animate"] = r["mode"] in _ANIMATED

    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for s in scenes:
        counts[s["mode"]] += 1
    animated_ids = [s["id"] for s in scenes if s["animate"]]
    print(
        f"[modes] HIGH={counts['HIGH']} MEDIUM={counts['MEDIUM']} LOW={counts['LOW']} "
        f"(cap ~{max_animated}). Animated beats: {animated_ids}"
    )
    return scenes_path
