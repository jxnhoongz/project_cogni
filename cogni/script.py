"""Stage 2: script — outline.json -> scenes.json + recording_script.txt.

Two model passes:
  1. narration_en (strong model): turn the outline into a coherent long-form
     script with a POINT OF VIEW (not a summary), broken into scenes. Each scene
     also gets an on_screen_text caption and an image_prompt.
  2. narration_km (Gemini): render each scene's meaning into NATURAL SPOKEN
     Khmer — how a Cambodian narrator would actually say it aloud, not a literal
     translation. Uses khmer_style_examples.txt as few-shot if present.

Then writes the scenes.json backbone and a recording_script.txt for the user to
read aloud — and STOPS. Recording is the user's job.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .config import ROOT, load_config, resolve_path
from .llm import call_stage

# Khmer and Thai are neighboring scripts; a model can occasionally drift from one
# to the other. We detect Thai/Lao characters as a contamination guard.
_THAI_LAO_RE = re.compile(r"[฀-໿]")

_SYSTEM_EN = (
    "You are a sharp, honest video essayist writing long-form YouTube narration "
    "for ONE narrator to read aloud. You take a real point of view — you never "
    "just summarize. You return only valid JSON."
)

_SYSTEM_KM = (
    "You are a Cambodian narrator. You render meaning into natural, SPOKEN Khmer "
    "— the way a real person would say it out loud in a video, not a literal or "
    "formal written translation. You write ONLY in Khmer script, never Thai or Lao. "
    "You return only valid JSON."
)

# Translate one scene per call (small = fast and never near the CLI timeout),
# run concurrently.
_KM_WORKERS = 4
_KM_RETRIES = 3


def _build_en_prompt(outline: dict[str, Any], angle: str, lo: int, hi: int) -> str:
    ideas = "\n".join(
        f"  - {k['title']}: {k['summary']}" for k in outline["key_ideas"]
    )
    return (
        f"Book: {outline['title']}"
        + (f" by {outline['author']}" if outline.get("author") else "")
        + "\n"
        f"Thesis: {outline['thesis']}\n\n"
        f"Key ideas:\n{ideas}\n\n"
        f"POINT OF VIEW (follow this closely):\n{angle}\n\n"
        f"Write the narration for a long-form video as a coherent arc: open with a "
        f"hook that states your stance; cover the genuinely useful ideas; push back "
        f"honestly on what is weak, vague, or overstated; address whether it applies "
        f"to the audience's real life; close with your actual take. Do NOT just list "
        f"the ideas.\n\n"
        f"Return JSON: {{\"scenes\": [ {{\"narration_en\": ..., \"on_screen_text\": "
        f"..., \"image_prompt\": ...}}, ... ]}} with between {lo} and {hi} scenes.\n"
        f"- narration_en: what the narrator says in this scene. First person, "
        f"spoken style, natural to read aloud (about 2-5 sentences).\n"
        f"- on_screen_text: a very short caption for the screen (<= 6 words), or "
        f"\"\" if none.\n"
        f"- image_prompt: describe ONE still image for this scene — concrete "
        f"subject and composition. IMPORTANT: no realistic human faces or hands; "
        f"favor landscapes, silhouettes, objects, symbolic imagery, or figures seen "
        f"from behind or far away. Do not mention art style (added separately)."
    )


def _km_scene_prompt(en_text: str, examples: str | None, remind: bool) -> str:
    fewshot = ""
    if examples:
        fewshot = (
            "Examples of the narrator's own natural spoken Khmer style — match "
            "this voice:\n" + examples.strip() + "\n\n"
        )
    reminder = ""
    if remind:
        reminder = (
            "\nCRITICAL: your previous attempt used Thai characters. Use ONLY Khmer "
            "script (អក្សរខ្មែរ) — zero Thai or Lao."
        )
    return (
        fewshot
        + "Render the meaning of this line into natural SPOKEN Khmer — the way a "
        "Cambodian narrator would say it aloud, NOT a literal word-for-word "
        "translation. Keep roughly the same length and beats.\n\n"
        "Write ONLY in Khmer script (អក្សរខ្មែរ). Do NOT use any Thai or Lao "
        "characters. Proper names and book titles may stay in Latin letters.\n"
        "Output only the Khmer sentence(s) — no quotes, no English, no notes."
        + reminder
        + f"\n\nLINE: {en_text}"
    )


def _translate_km_scene(
    scene_id: int,
    en_text: str,
    examples: str | None,
    cfg: dict[str, Any],
) -> tuple[int, str]:
    """Translate one scene to clean Khmer, retrying on any failure (empty content,
    transient/timeout error, or Thai/Lao contamination)."""
    last_reason = "unknown"
    for attempt in range(_KM_RETRIES):
        try:
            text = call_stage(
                cfg,
                "script_km",
                _km_scene_prompt(en_text, examples, remind=attempt > 0),
                system=_SYSTEM_KM,
                json_out=False,
            )
        except RuntimeError as e:
            last_reason = str(e)
            continue
        km = str(text).strip().strip('"').strip()
        if not km:
            last_reason = "empty response"
            continue
        if _THAI_LAO_RE.search(km):
            last_reason = "Thai/Lao contamination"
            continue
        return scene_id, km
    raise RuntimeError(
        f"script: scene {scene_id} Khmer failed after {_KM_RETRIES} attempts "
        f"(last: {last_reason})."
    )


def _translate_km(
    en_scenes: list[dict[str, Any]],
    examples: str | None,
    cfg: dict[str, Any],
) -> dict[int, str]:
    """Translate every scene, one small concurrent call each."""
    with ThreadPoolExecutor(max_workers=_KM_WORKERS) as pool:
        results = pool.map(
            lambda item: _translate_km_scene(item[0], item[1]["narration_en"], examples, cfg),
            list(enumerate(en_scenes, 1)),
        )
        return dict(results)


def _load_examples(cfg: dict[str, Any]) -> str | None:
    name = cfg["script"].get("khmer_examples")
    if not name:
        return None
    path = ROOT / name
    if path.exists() and path.read_text(encoding="utf-8").strip():
        print(f"[script] using Khmer few-shot examples from {path.name}")
        return path.read_text(encoding="utf-8")
    return None


def script(
    *,
    force: bool = False,
    angle: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> Path:
    """Generate scenes.json + recording_script.txt from outline.json, then STOP."""
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

    # Pass 1 — English narration + captions + image prompts (Claude, subscription).
    print("[script] writing English narration ...")
    en_data = call_stage(
        cfg,
        "script_en",
        _build_en_prompt(outline, the_angle, lo, hi),
        system=_SYSTEM_EN,
        json_out=True,
    )
    en_scenes = _validate_en(en_data)
    print(f"[script] {len(en_scenes)} scenes drafted.")

    # Pass 2 — natural spoken Khmer for every scene (one call), with a
    # contamination guard + retry.
    examples = _load_examples(cfg)
    print(f"[script] translating {len(en_scenes)} scenes to spoken Khmer ...")
    km_by_id = _translate_km(en_scenes, examples, cfg)

    scenes = []
    for i, en in enumerate(en_scenes, 1):
        scenes.append(
            {
                "id": i,
                "narration_en": en["narration_en"],
                "narration_km": km_by_id[i],
                "on_screen_text": en.get("on_screen_text", ""),
                "image_prompt": en["image_prompt"],
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

    rec_path = resolve_path(cfg, "recording_script")
    rec_path.write_text(_recording_script(doc), encoding="utf-8")

    print(f"[script] wrote {scenes_path.name} and {rec_path.name} ({len(scenes)} scenes).")
    print(
        "[script] STOP: edit the Khmer if needed, then record one .wav per scene "
        f"into {resolve_path(cfg, 'audio')}/ (scene_001.wav ...) and run `check-audio`."
    )
    return scenes_path


def _recording_script(doc: dict[str, Any]) -> str:
    out = [
        f"RECORDING SCRIPT — {doc['project_title']}",
        f"{len(doc['scenes'])} scenes. Read each Khmer line aloud, one recording per scene.",
        "Save recordings as: audio/scene_001.wav, audio/scene_002.wav, ...",
        "The English line is only there so you know the meaning — you read the Khmer.",
        "",
    ]
    for s in doc["scenes"]:
        out.append(f"════════ Scene {s['id']:>2} ════════")
        out.append(f"EN (meaning): {s['narration_en']}")
        out.append(f"KM (read this): {s['narration_km']}")
        out.append("")
    return "\n".join(out)


def _validate_en(data: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("script: English pass returned no scenes")
    clean = []
    for i, s in enumerate(scenes, 1):
        if not isinstance(s, dict):
            raise RuntimeError(f"script: EN scene #{i} is not an object")
        narration = str(s.get("narration_en") or "").strip()
        image_prompt = str(s.get("image_prompt") or "").strip()
        if not narration:
            raise RuntimeError(f"script: EN scene #{i} has no narration_en")
        if not image_prompt:
            raise RuntimeError(f"script: EN scene #{i} has no image_prompt")
        clean.append(
            {
                "narration_en": narration,
                "on_screen_text": str(s.get("on_screen_text") or "").strip(),
                "image_prompt": image_prompt,
            }
        )
    return clean
