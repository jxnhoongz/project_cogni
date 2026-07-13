"""Stage 2: script — outline.json -> scenes.json.

Turn the outline into a coherent script with a POINT OF VIEW — a verdict, not a
summary — broken into scenes (narration + on_screen_text + image_prompt). Two modes
(config.yaml script.mode):

  - "short": one model pass, min/max_scenes scenes (~4-5 min). Fast, cheap; for tests.
  - "long":  a structure pass plans chapters (cold open -> chapters -> verdict close),
             then ONE focused pass per chapter produces its scenes. Keeps each call
             sharp while reaching a ~30-45 min deep-dive. Scenes are concatenated with
             continuous ids; chapter titles are recorded on the doc and each scene.

Both modes emit the same per-scene schema, so every downstream stage (script-review,
visuals, review, narrate, images, animate, assemble) works unchanged.
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

# Shared scene-writing rules, used by the short pass and every chapter pass.
_SCENE_RULES = (
    "- narration: what the narrator says in this scene. First person, spoken, natural "
    "to hear aloud.\n"
    "- on_screen_text: a very short caption for the screen (<= 6 words), or \"\" if none.\n"
    "- image_prompt: describe ONE still image for this scene — concrete subject and "
    "composition. IMPORTANT: no realistic human faces or hands; favor landscapes, "
    "silhouettes, objects, symbolic imagery, or figures seen from behind or far away. "
    "Do not mention art style (added separately)."
)


def _scene_record(i: int, s: dict[str, Any], chapter: str | None = None) -> dict[str, Any]:
    """Build one scenes.json record (the schema every stage downstream expects)."""
    return {
        "id": i,
        "narration": s["narration"],
        "on_screen_text": s.get("on_screen_text", ""),
        "image_prompt": s["image_prompt"],   # seed still; `visuals` refines it
        "chapter": chapter,                   # long mode: which chapter this scene is in
        # Filled by the `visuals` stage (two keyframes + a motion prompt):
        "start_image_prompt": "",
        "end_image_prompt": "",
        "video_prompt": "",
        "review": None,                       # set by the visuals `review` gate
        "narration_review": None,             # set by `script-review`
        "animate": False,
        "audio_path": None,
        "image_path": None,
        "end_image_path": None,               # second keyframe still (animate scenes)
        "clip_path": None,
        "duration_sec": None,
    }


# --- short mode --------------------------------------------------------------

def _build_prompt(outline: dict[str, Any], angle: str, lo: int, hi: int) -> str:
    ideas = "\n".join(f"  - {k['title']}: {k['summary']}" for k in outline["key_ideas"])
    return (
        f"Book: {outline['title']}"
        + (f" by {outline['author']}" if outline.get("author") else "")
        + "\n"
        f"Thesis: {outline['thesis']}\n\n"
        f"Key ideas:\n{ideas}\n\n"
        f"POINT OF VIEW (follow this closely):\n{angle}\n\n"
        f"Write the narration for a long-form video as a coherent arc:\n"
        f"- OPEN (scene 1) with a PROVOCATIVE QUESTION — the real question this book "
        f"promises to answer, framed so the viewer feels it personally (their money, "
        f"time, or life), and hint at who benefits from the usual answer. Make them "
        f"need to know. Do NOT state your verdict or stance yet, and do NOT open with "
        f"'my honest verdict' or any 'in this video' throat-clearing.\n"
        f"- Then investigate: cover the genuinely useful ideas; push back honestly on "
        f"what is weak, vague, or overstated; say who it actually helps.\n"
        f"- CLOSE with your actual verdict — the stance you earned along the way.\n"
        f"Do NOT just list the ideas.\n\n"
        f"Return JSON: {{\"scenes\": [ {{\"narration\": ..., \"on_screen_text\": ..., "
        f"\"image_prompt\": ...}}, ... ]}} with between {lo} and {hi} scenes.\n"
        f"Each scene's narration is about 2-5 sentences.\n"
        f"{_SCENE_RULES}"
    )


def _generate_short(cfg: dict[str, Any], outline: dict[str, Any], angle: str):
    sc = cfg["script"]
    lo, hi = sc["min_scenes"], sc["max_scenes"]
    print("[script] short mode — writing narration ...")
    data = call_stage(
        cfg, "script", _build_prompt(outline, angle, lo, hi),
        system=_SYSTEM, json_out=True,
    )
    scenes_in = _validate(data)
    print(f"[script] {len(scenes_in)} scenes drafted.")
    return [_scene_record(i, s) for i, s in enumerate(scenes_in, 1)], {}


# --- long mode (chaptered) ---------------------------------------------------

def _build_structure_prompt(
    outline: dict[str, Any], angle: str, lo_ch: int, hi_ch: int, minutes: int
) -> str:
    ideas = "\n".join(f"  - {k['title']}: {k['summary']}" for k in outline["key_ideas"])
    return (
        f"Book: {outline['title']}"
        + (f" by {outline['author']}" if outline.get("author") else "")
        + "\n"
        f"Thesis: {outline['thesis']}\n\nKey ideas:\n{ideas}\n\n"
        f"POINT OF VIEW (follow this closely):\n{angle}\n\n"
        f"Plan a ~{minutes}-minute long-form video as a CHAPTER OUTLINE that builds ONE "
        f"honest verdict across the whole runtime — not a summary, not a list. Use "
        f"between {lo_ch} and {hi_ch} chapters.\n"
        f"- Chapter 1 is the COLD OPEN: it opens on a provocative question (the real "
        f"question the book promises to answer, felt personally) — NOT the verdict.\n"
        f"- Middle chapters investigate: the genuinely useful ideas, and honest pushback "
        f"on what is weak, vague, or overstated. Each middle chapter takes a distinct "
        f"angle so they don't repeat each other.\n"
        f"- The FINAL chapter delivers the earned verdict and who it actually helps.\n\n"
        f'Return JSON: {{"chapters": [{{"title": ..., "focus": ...}}, ...]}}. '
        f"title = a short chapter title; focus = 1-2 sentences on what this chapter "
        f"covers and its role in the arc."
    )


def _build_chapter_prompt(
    outline: dict[str, Any], angle: str, chapter: dict[str, Any],
    idx: int, total: int, prior_titles: list[str], lo_sc: int, hi_sc: int,
) -> str:
    if idx == 1:
        role = ("the COLD OPEN — open on a provocative question that makes the viewer "
                "feel it personally; do NOT state the verdict, no 'in this video' intro")
    elif idx == total:
        role = "the FINAL chapter — deliver the earned verdict and who it actually helps"
    else:
        role = "a middle chapter — investigate honestly: useful ideas and fair pushback"
    prior = "; ".join(prior_titles) if prior_titles else "(this is the first chapter)"
    return (
        f"Book: {outline['title']}\nThesis: {outline['thesis']}\n\n"
        f"POINT OF VIEW (follow this closely):\n{angle}\n\n"
        f"You are writing ONE chapter of a long-form video. Chapters already written: "
        f"{prior}.\n"
        f"Now write CHAPTER {idx} of {total}: \"{chapter['title']}\".\n"
        f"Chapter focus: {chapter.get('focus', '')}\n"
        f"Role in the arc: {role}.\n\n"
        f"Write this chapter as {lo_sc}-{hi_sc} scenes of spoken narration that flow as "
        f"one continuous stretch — do NOT read the chapter title aloud, do NOT say 'in "
        f"this chapter', and pick up naturally from what came before. First person, "
        f"natural to hear aloud; each scene about 3-6 sentences.\n\n"
        f"Return JSON: {{\"scenes\": [ {{\"narration\": ..., \"on_screen_text\": ..., "
        f"\"image_prompt\": ...}}, ... ]}}.\n"
        f"{_SCENE_RULES}"
    )


def _validate_chapters(data: dict[str, Any]) -> list[dict[str, str]]:
    chapters = data.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise RuntimeError("script(long): structure pass returned no chapters")
    clean = []
    for i, c in enumerate(chapters, 1):
        if not isinstance(c, dict):
            raise RuntimeError(f"script(long): chapter #{i} is not an object")
        title = str(c.get("title") or "").strip() or f"Chapter {i}"
        clean.append({"title": title, "focus": str(c.get("focus") or "").strip()})
    return clean


def _generate_long(cfg: dict[str, Any], outline: dict[str, Any], angle: str):
    lg = cfg["script"].get("long", {})
    lo_ch, hi_ch = lg.get("min_chapters", 5), lg.get("max_chapters", 7)
    lo_sc, hi_sc = lg.get("min_scenes_per_chapter", 10), lg.get("max_scenes_per_chapter", 14)
    minutes = lg.get("target_minutes", 37)

    print(f"[script] long mode (~{minutes} min) — planning chapters ...")
    struct = call_stage(
        cfg, "script", _build_structure_prompt(outline, angle, lo_ch, hi_ch, minutes),
        system=_SYSTEM, json_out=True,
    )
    chapters = _validate_chapters(struct)
    print(f"[script] {len(chapters)} chapters planned. Writing chapter by chapter ...")

    records: list[tuple[dict[str, Any], str]] = []
    prior: list[str] = []
    total = len(chapters)
    for idx, ch in enumerate(chapters, 1):
        data = call_stage(
            cfg, "script",
            _build_chapter_prompt(outline, angle, ch, idx, total, prior, lo_sc, hi_sc),
            system=_SYSTEM, json_out=True,
        )
        chap = _validate(data)
        records.extend((s, ch["title"]) for s in chap)
        prior.append(ch["title"])
        print(f"[script]   chapter {idx}/{total} \"{ch['title']}\": {len(chap)} scenes "
              f"(running total {len(records)})")

    scenes = [_scene_record(i, s, chapter=title) for i, (s, title) in enumerate(records, 1)]
    return scenes, {"chapters": [c["title"] for c in chapters]}


# --- entry point -------------------------------------------------------------

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
    the_angle = angle or sc["angle"]
    mode = str(sc.get("mode", "short")).lower()

    if mode == "long":
        scenes, extra = _generate_long(cfg, outline, the_angle)
    else:
        scenes, extra = _generate_short(cfg, outline, the_angle)

    doc = {
        "project_title": outline["title"],
        "thesis": outline["thesis"],
        **extra,
        "scenes": scenes,
    }
    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[script] wrote {scenes_path.name} ({len(scenes)} scenes, mode={mode}). "
          "Next: `script-review`, then `narrate`.")
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
