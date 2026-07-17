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
    "You are Cognibot, narrator of a channel that reads books so lazy humans don't "
    "have to. You speak clear, natural, everyday English — never broken robot-speak "
    "(that lives only on the channel banner). You are blunt, a little funny, and you "
    "TEACH: an honest point of view, a verdict, not a summary. You teach a book's ideas "
    "by telling the story of one relatable person it applies to, and you judge the book "
    "as you go. You return only valid JSON."
)

# Shared scene-writing rules, used by the short pass and every chapter pass.
_SCENE_RULES = (
    "- narration: what Cognibot says in this beat. Clear, natural, spoken first person. "
    "Teach through the character's story and give your honest take on the book; never "
    "flatly summarize.\n"
    "- on_screen_text: a very short caption for the screen (<= 6 words), or \"\" if none.\n"
    "- image_prompt: describe ONE still image for THIS beat — the single concrete moment "
    "being narrated right now, not the scene's whole idea. When a person appears it is the "
    "recurring protagonist as a stylized, faceted LOW-POLY figure — a clear low-poly face "
    "is good, never photorealistic; keep them the SAME person for continuity. Otherwise use "
    "objects or symbolic imagery. Do not mention art style (added separately)."
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
        "fact_review": None,                  # set by `fact-check` (narration vs book.md)
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
        f"You are Cognibot. Teach this book by telling the story of ONE relatable person "
        f"it applies to — a specific everyperson who fits the book's world. Invent them: "
        f"give them a name, an ordinary life, and a real problem. Teach each key idea "
        f"through what happens to this character, and JUDGE the book honestly as you go.\n\n"
        f"Write the narration as a coherent arc:\n"
        f"- COLD OPEN (scene 1): the character's relatable problem, framed as the real "
        f"question this book promises to answer, felt personally (their money, time, or "
        f"life). Do NOT state your verdict yet; no 'in this video' throat-clearing.\n"
        f"- BODY: the character runs into each key idea. Teach the idea through their "
        f"story, then step out and give Cognibot's honest take — what the book nails, what "
        f"it skips or oversells, who it fails.\n"
        f"- CLOSE: the character's outcome + your earned overall verdict + who it actually "
        f"helps.\n"
        f"Never just list the ideas. Keep the character consistent throughout.\n\n"
        f'Return JSON: {{"character": {{"name": <string>, "description": <one sentence on '
        f'how they look as a recurring low-poly character with a clear face — concrete, non-photorealistic>}}, "scenes": [ {{"narration": ..., '
        f'"on_screen_text": ..., "image_prompt": ...}}, ... ]}} with between {lo} and {hi} '
        f"scenes. Each scene is ONE beat: 1-3 sentences of narration and an image for that "
        f"single moment.\n"
        f"{_SCENE_RULES}"
    )


def _generate_short(cfg: dict[str, Any], outline: dict[str, Any], angle: str):
    sc = cfg["script"]
    lo, hi = sc["min_scenes"], sc["max_scenes"]
    print("[script] short mode — Cognibot writing the character's story ...")
    data = call_stage(
        cfg, "script", _build_prompt(outline, angle, lo, hi),
        system=_SYSTEM, json_out=True,
    )
    scenes_in = _validate(data)
    character = _validate_character(data)
    who = character["name"] if character else "(no named character)"
    print(f"[script] {len(scenes_in)} scenes drafted around {who}.")
    return [_scene_record(i, s) for i, s in enumerate(scenes_in, 1)], {"character": character}


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
        f"You are Cognibot, planning a ~{minutes}-minute video that TEACHES this book by "
        f"following ONE relatable protagonist's story across the whole runtime — judging "
        f"the book honestly as you go. Not a summary, not a list.\n\n"
        f"First, invent the protagonist: a specific everyperson who fits the book's world, "
        f"with a name, an ordinary life, and a real problem the book speaks to.\n"
        f"Then plan {lo_ch}-{hi_ch} chapters that follow that same person:\n"
        f"- Chapter 1 is the COLD OPEN: their relatable problem, framed as the real "
        f"question the book promises to answer (felt personally) — NOT the verdict.\n"
        f"- Middle chapters each take a distinct idea and put the character through it, with "
        f"Cognibot's honest take on that specific idea, judged on its own terms. Distinct "
        f"angles, no repeats.\n"
        f"- The FINAL chapter delivers the character's outcome, then the earned verdict built "
        f"out of THIS book's own specifics: the one idea that most survives scrutiny and the "
        f"one claim that least survives it, both named concretely, with the verdict landing "
        f"wherever those two leave it.\n\n"
        f'Return JSON: {{"character": {{"name": <string>, "description": <one sentence on '
        f'how they look as a recurring low-poly character with a clear face — concrete, non-photorealistic>}}, "chapters": [{{"title": ..., '
        f'"focus": ...}}, ...]}}. title = short chapter title; focus = 1-2 sentences on what '
        f"this chapter covers and its role in the character's arc."
    )


def _build_chapter_prompt(
    outline: dict[str, Any], angle: str, character: dict[str, str] | None,
    chapter: dict[str, Any], idx: int, total: int, prior_titles: list[str],
    lo_sc: int, hi_sc: int,
) -> str:
    if idx == 1:
        role = ("the COLD OPEN — open on the character's relatable problem as a provocative "
                "question; do NOT state the verdict, no 'in this video' intro")
    elif idx == total:
        role = ("the FINAL chapter — the character's outcome, then the earned verdict built out of "
                "THIS book's own specifics: the one idea that most survives scrutiny and the one "
                "claim that least survives it, both named concretely, with the verdict landing "
                "wherever those two leave it")
    else:
        role = "a middle chapter — teach one idea through the character and judge the book honestly"
    prior = "; ".join(prior_titles) if prior_titles else "(this is the first chapter)"
    who = (f"{character['name']} — {character['description']}"
           if character else "the recurring protagonist")
    return (
        f"Book: {outline['title']}\nThesis: {outline['thesis']}\n\n"
        f"POINT OF VIEW (follow this closely):\n{angle}\n\n"
        f"You are Cognibot, writing ONE chapter of a long-form video that follows ONE "
        f"protagonist: {who}. Keep this SAME person consistent.\n"
        f"Chapters already written: {prior}.\n"
        f"Now write CHAPTER {idx} of {total}: \"{chapter['title']}\".\n"
        f"Chapter focus: {chapter.get('focus', '')}\n"
        f"Role in the arc: {role}.\n\n"
        f"Write this chapter as {lo_sc}-{hi_sc} beats that follow the character and flow as "
        f"one continuous stretch — do NOT read the chapter title aloud, do NOT say 'in this "
        f"chapter', pick up naturally from what came before. Teach each idea through what "
        f"happens to the character, and give Cognibot's honest take. Each beat = 1-3 "
        f"sentences of narration and an image for that single moment.\n\n"
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
    minutes = lg.get("target_minutes", 30)

    print(f"[script] long mode (~{minutes} min) — Cognibot planning the character's chapters ...")
    struct = call_stage(
        cfg, "script", _build_structure_prompt(outline, angle, lo_ch, hi_ch, minutes),
        system=_SYSTEM, json_out=True,
    )
    character = _validate_character(struct)
    chapters = _validate_chapters(struct)
    who = character["name"] if character else "(no named character)"
    print(f"[script] {len(chapters)} chapters planned around {who}. Writing chapter by chapter ...")

    records: list[tuple[dict[str, Any], str]] = []
    prior: list[str] = []
    total = len(chapters)
    for idx, ch in enumerate(chapters, 1):
        data = call_stage(
            cfg, "script",
            _build_chapter_prompt(outline, angle, character, ch, idx, total, prior, lo_sc, hi_sc),
            system=_SYSTEM, json_out=True,
        )
        chap = _validate(data)
        records.extend((s, ch["title"]) for s in chap)
        prior.append(ch["title"])
        print(f"[script]   chapter {idx}/{total} \"{ch['title']}\": {len(chap)} scenes "
              f"(running total {len(records)})")

    scenes = [_scene_record(i, s, chapter=title) for i, (s, title) in enumerate(records, 1)]
    return scenes, {"character": character, "chapters": [c["title"] for c in chapters]}


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


def _validate_character(data: dict[str, Any]) -> dict[str, str] | None:
    """Extract the invented protagonist; tolerate absence (returns None)."""
    c = data.get("character")
    if not isinstance(c, dict):
        return None
    name = str(c.get("name") or "").strip()
    desc = str(c.get("description") or "").strip()
    if not (name and desc):
        return None
    return {"name": name, "description": desc}
