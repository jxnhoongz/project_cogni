"""Stage 2: script — outline.json -> scenes.json.

One model pass (strong model): turn the outline into a coherent long-form script
with a POINT OF VIEW — a verdict, not a summary — broken into scenes. Each scene
gets narration (spoken, to be heard), an on_screen_text caption, and an
image_prompt. The narration is what the TTS narrator reads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_config, resolve_path
from .llm import call_stage

_SYSTEM = (
    "You are a sharp, honest video essayist writing long-form YouTube narration "
    "to be read aloud by a narrator. You take a real point of view — you never "
    "just summarize. You return only valid JSON."
)


def _build_prompt(outline: dict[str, Any], angle: str, lo: int, hi: int) -> str:
    ideas = "\n".join(f"  - {k['title']}: {k['summary']}" for k in outline["key_ideas"])
    return (
        f"Book: {outline['title']}"
        + (f" by {outline['author']}" if outline.get("author") else "")
        + "\n"
        f"Thesis: {outline['thesis']}\n\n"
        f"Key ideas:\n{ideas}\n\n"
        f"POINT OF VIEW (follow this closely):\n{angle}\n\n"
        f"Write the narration for a long-form video as a coherent arc: open with a "
        f"hook that states your stance; cover the genuinely useful ideas; push back "
        f"honestly on what is weak, vague, or overstated; say who it actually helps; "
        f"close with your actual verdict. Do NOT just list the ideas.\n\n"
        f"Return JSON: {{\"scenes\": [ {{\"narration\": ..., \"on_screen_text\": ..., "
        f"\"image_prompt\": ...}}, ... ]}} with between {lo} and {hi} scenes.\n"
        f"- narration: what the narrator says in this scene. First person, spoken, "
        f"natural to hear aloud (about 2-5 sentences).\n"
        f"- on_screen_text: a very short caption for the screen (<= 6 words), or "
        f"\"\" if none.\n"
        f"- image_prompt: describe ONE still image for this scene — concrete subject "
        f"and composition. IMPORTANT: no realistic human faces or hands; favor "
        f"landscapes, silhouettes, objects, symbolic imagery, or figures seen from "
        f"behind or far away. Do not mention art style (added separately)."
    )


def script(
    *,
    force: bool = False,
    angle: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> Path:
    """Generate scenes.json from outline.json (a verdict, not a summary)."""
    cfg = cfg or load_config()
    outline_path = resolve_path(cfg, "outline")
    if not outline_path.exists():
        raise FileNotFoundError(
            f"{outline_path} not found — run `ingest` first to create it."
        )

    scenes_path = resolve_path(cfg, "scenes")
    if scenes_path.exists() and not force:
        print(f"[script] cached — {scenes_path} exists (use --force to regenerate)")
        return scenes_path

    outline = json.loads(outline_path.read_text(encoding="utf-8"))
    sc = cfg["script"]
    lo, hi = sc["min_scenes"], sc["max_scenes"]
    the_angle = angle or sc["angle"]

    print("[script] writing narration ...")
    data = call_stage(
        cfg,
        "script",
        _build_prompt(outline, the_angle, lo, hi),
        system=_SYSTEM,
        json_out=True,
    )
    scenes_in = _validate(data)
    print(f"[script] {len(scenes_in)} scenes drafted.")

    scenes = []
    for i, s in enumerate(scenes_in, 1):
        scenes.append(
            {
                "id": i,
                "narration": s["narration"],
                "on_screen_text": s.get("on_screen_text", ""),
                "image_prompt": s["image_prompt"],
                "animate": False,
                "audio_path": None,
                "image_path": None,
                "clip_path": None,
                "duration_sec": None,
            }
        )

    doc = {
        "project_title": outline["title"],
        "thesis": outline["thesis"],
        "scenes": scenes,
    }
    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[script] wrote {scenes_path.name} ({len(scenes)} scenes). Next: `narrate`.")
    return scenes_path


def _validate(data: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("script: model returned no scenes")
    clean = []
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"script: scene #{i} is not an object")
        narration = str(s.get("narration") or "").strip()
        image_prompt = str(s.get("image_prompt") or "").strip()
        if not narration:
            raise RuntimeError(f"script: scene #{i} has no narration")
        if not image_prompt:
            raise RuntimeError(f"script: scene #{i} has no image_prompt")
        clean.append(
            {
                "narration": narration,
                "on_screen_text": str(s.get("on_screen_text") or "").strip(),
                "image_prompt": image_prompt,
            }
        )
    return clean
