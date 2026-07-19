"""Stage 2: script — outline.json -> scenes.json.

Turn the outline into a coherent script with a POINT OF VIEW — a verdict, not a
summary — broken into scenes (narration + on_screen_text + image_prompt). Two modes
(config.yaml script.mode):

  - "short": one model pass, min/max_scenes scenes (~4-5 min). Fast, cheap; for tests.
  - "long":  a Story Architect pass designs a story bible (protagonist, argument,
             wager, acts), then ONE focused pass per act produces its scenes. Keeps
             each call sharp while reaching a ~30-45 min deep-dive. Scenes are
             concatenated with continuous ids; act titles are recorded on the doc
             (as "chapters") and each scene; the full bible is recorded as "story".

Both modes emit the same per-scene schema, so every downstream stage (script-review,
visuals, review, narrate, images, animate, assemble) works unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_config, resolve_path
from .llm import call_stage
from .pronounce import avoid_clause

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
    "Teach through the character's story and give Cognibot's pointed, specific judgement; "
    "never flatly summarize.\n"
    "- on_screen_text: a very short caption for the screen (<= 6 words), or \"\" if none.\n"
    "- image_prompt: describe ONE still image for THIS beat — the single concrete moment "
    "being narrated right now, not the scene's whole idea. When a person appears it is the "
    "recurring protagonist as a stylized, faceted LOW-POLY figure — a clear low-poly face "
    "is good, never photorealistic; keep them the SAME person for continuity. Otherwise use "
    "objects or symbolic imagery. Do not mention art style (added separately).\n"
    f"- {avoid_clause()}"
)


def _shapes_from_docs(docs: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Story-shapes already used by other books — to force variety."""
    stances, openings, wagers = set(), set(), set()
    for d in docs:
        st = (d or {}).get("story") or {}
        if s := str((st.get("argument") or {}).get("stance") or "").strip():
            stances.add(s)
        if o := str(st.get("opening_move") or "").strip():
            openings.add(o)
        if w := str((st.get("wager") or {}).get("book_claim_on_trial") or "").strip():
            wagers.add(w)
    return {"stances": sorted(stances), "openings": sorted(openings), "wagers": sorted(wagers)}


def _prior_story_shapes(cfg: dict[str, Any]) -> dict[str, list[str]]:
    """Collect prior story-shapes from every OTHER book under projects/."""
    from .config import PROJECTS_DIR, resolve_path
    active = resolve_path(cfg, "scenes").resolve()
    docs = []
    for f in PROJECTS_DIR.rglob("scenes.json"):
        try:
            if f.resolve() == active:
                continue
            docs.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return _shapes_from_docs(docs)


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

def _build_architect_prompt(outline: dict[str, Any], angle: str, lo_ch: int, hi_ch: int,
                            minutes: int, shapes: dict[str, list[str]]) -> str:
    ideas = "\n".join(f"  - {k['title']}: {k['summary']}" for k in outline["key_ideas"])
    used = ""
    if shapes.get("stances") or shapes.get("openings") or shapes.get("wagers"):
        used = (
            "\nOther videos on this channel already used these — pick DIFFERENT ones:\n"
            f"  - verdict stances used: {', '.join(shapes['stances']) or 'none'}\n"
            f"  - opening moves used: {', '.join(shapes['openings']) or 'none'}\n"
            f"  - claims already put on trial: {', '.join(shapes['wagers']) or 'none'}\n"
        )
    return (
        f"Book: {outline['title']}"
        + (f" by {outline['author']}" if outline.get("author") else "")
        + f"\nThesis: {outline['thesis']}\n\nKey ideas:\n{ideas}\n\n"
        f"Stance to hold (do NOT import a house opinion; make the verdict specific to THIS book):\n{angle}\n\n"
        f"You are Cognibot, ARCHITECTING a ~{minutes}-minute video. Design a STORY, not a summary. "
        f"The golden rule: TEST the book, don't ILLUSTRATE it. A protagonist who merely demonstrates each "
        f"idea in order is a failure. Instead the protagonist must make a real decision where one of the "
        f"book's central claims is on trial — and sometimes the book's advice must LOSE. The verdict is "
        f"EARNED by that outcome, never asserted, and is WITHHELD until the end.\n"
        f"{used}\n"
        f"Design the whole thing, then output it as JSON:\n"
        f"{{\n"
        f'  "protagonist": {{"name": <string>, "description": <one sentence, recurring low-poly look with a '
        f'clear face, non-photorealistic>, "wound": <one specific bit of history/shame that makes them care '
        f'— keep it light, this stays a funny/useful channel>}},\n'
        f'  "argument": {{"stance": <"mostly-right" | "mostly-wrong" | "dangerously-half-right">, '
        f'"claim": <one sentence someone could disagree with, ABOUT THIS BOOK — the earned verdict>}},\n'
        f'  "wager": {{"book_claim_on_trial": <which claim the protagonist bets on>, "decision": <the real '
        f'decision with a downside>, "outcome": <"book-wins" | "book-loses" | "mixed">}},\n'
        f'  "plant": <something set up early>, "payoff": <how it detonates late>,\n'
        f'  "closing_scene": <one concrete final moment that embodies the argument — a scene, not a '
        f'"who it is for" list>,\n'
        f'  "opening_move": <the KIND of cold open, different from the used ones above>,\n'
        f'  "voice_moves": [<1-2 moves only a bot could make: total recall of the whole text, catching the '
        f'book contradict itself>],\n'
        f'  "acts": [{{"title": <short>, "focus": <1-2 sentences>, "role": <its job in the arc>, '
        f'"ideas": [{{"idea": <which key idea>, "mode": <"tool" | "obstacle" | "failure" | "discovery">}}], '
        f'"carries": <"wager" | "plant" | "payoff" | "none">}}, ...]\n'
        f"}}\n"
        f"Plan {lo_ch}-{hi_ch} acts. Exactly one act carries the wager, one the payoff; ideas may enter out "
        f"of order. Act 1 is the cold open (the protagonist's problem as a live question — NOT the verdict)."
    )


def _build_act_prompt(outline: dict[str, Any], bible: dict[str, Any], act: dict[str, Any],
                      idx: int, total: int, prior_titles: list[str], lo_sc: int, hi_sc: int) -> str:
    p = bible["protagonist"]
    who = f"{p['name']} — {p['description']}" + (f" (wound: {p['wound']})" if p["wound"] else "")
    ideas = "; ".join(f"{i['idea']} (enters as {i['mode']})" for i in act["ideas"]) or "(no new book idea this act)"
    prior = "; ".join(prior_titles) if prior_titles else "(this is the first act)"
    carries = act["carries"]
    extra = ""
    if carries == "wager":
        w = bible["wager"]
        extra = (f"\nTHIS act carries the WAGER: {p['name']} makes this real decision — {w['decision']} — "
                 f"with '{w['book_claim_on_trial']}' on trial. Outcome: {w['outcome']}. If the book LOSES here, "
                 f"let it lose on-screen; do not rescue it. Real downside, real tension.")
    elif carries == "plant":
        extra = f"\nTHIS act plants: {bible['plant']} — set it up so it can pay off later; don't underline it."
    elif carries == "payoff":
        extra = (f"\nTHIS is where it all lands. Detonate the plant ({bible['payoff']}), then deliver the "
                 f"WITHHELD verdict for the first time: \"{bible['argument']['claim']}\". End on the closing "
                 f"scene — {bible['closing_scene']} — a concrete moment, NOT a 'who this is for' list.")
    voice = ", ".join(bible["voice_moves"])
    return (
        f"Book: {outline['title']}\nThesis: {outline['thesis']}\n\n"
        f"You are Cognibot, writing ONE act of a video that follows ONE protagonist: {who}. "
        f"Keep this SAME person consistent. Acts already written: {prior}.\n\n"
        f"Write ACT {idx} of {total}: \"{act['title']}\". Role in the arc: {act['role'] or '(continue the story)'}.\n"
        f"Focus: {act['focus']}\nBook ideas this act uses: {ideas}.{extra}\n\n"
        f"RULES:\n"
        f"- DRAMATIZE, do not explain. The protagonist ACTS, decides, or DISCOVERS the idea through friction — "
        f"never step out to lecture the framework at the viewer.\n"
        f"- Do NOT deliver the final verdict early. Middle acts raise questions; only the payoff act judges.\n"
        f"- No 'here's my take on this stretch' summaries, no 'X years later' unless it earns a real scene.\n"
        + (f"- Use a bot-only voice move where it fits: {voice} (a flex a human reviewer can't make).\n" if voice else "")
        + f"- Keep Cognibot blunt and funny; let specificity carry the bluntness (don't announce it).\n\n"
        f"Write {lo_sc}-{hi_sc} beats that flow as one continuous stretch — do NOT read the act title aloud. "
        f"Each beat = 1-3 sentences of narration and an image for that single moment.\n\n"
        f'Return JSON: {{"scenes": [{{"narration": ..., "on_screen_text": ..., "image_prompt": ...}}, ...]}}.\n'
        f"{_SCENE_RULES}"
    )


def _generate_long(cfg: dict[str, Any], outline: dict[str, Any], angle: str):
    lg = cfg["script"].get("long", {})
    lo_ch, hi_ch = lg.get("min_chapters", 5), lg.get("max_chapters", 7)
    lo_sc, hi_sc = lg.get("min_scenes_per_chapter", 10), lg.get("max_scenes_per_chapter", 14)
    minutes = lg.get("target_minutes", 30)

    print(f"[script] long mode (~{minutes} min) — Cognibot architecting the story ...")
    bible = _validate_story(call_stage(
        cfg, "script",
        _build_architect_prompt(outline, angle, lo_ch, hi_ch, minutes, _prior_story_shapes(cfg)),
        system=_SYSTEM, json_out=True,
    ))
    character = bible["protagonist"]
    acts = bible["acts"]
    print(f"[script] story bible ready — {character['name']}, {len(acts)} acts, "
          f"stance={bible['argument']['stance']}. Writing act by act ...")

    records: list[tuple[dict[str, Any], str]] = []
    prior: list[str] = []
    total = len(acts)
    for idx, act in enumerate(acts, 1):
        data = call_stage(
            cfg, "script",
            _build_act_prompt(outline, bible, act, idx, total, prior, lo_sc, hi_sc),
            system=_SYSTEM, json_out=True,
        )
        chap = _validate(data)
        records.extend((s, act["title"]) for s in chap)
        prior.append(act["title"])
        print(f"[script]   act {idx}/{total} \"{act['title']}\": {len(chap)} scenes "
              f"(running total {len(records)})")

    scenes = [_scene_record(i, s, chapter=title) for i, (s, title) in enumerate(records, 1)]
    return scenes, {"character": character, "chapters": [a["title"] for a in acts], "story": bible}


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


_STANCES = {"mostly-right", "mostly-wrong", "dangerously-half-right"}
_OUTCOMES = {"book-wins", "book-loses", "mixed"}
_MODES = {"tool", "obstacle", "failure", "discovery"}
_CARRIES = {"wager", "plant", "payoff", "none"}


def _validate_story(story: dict[str, Any]) -> dict[str, Any]:
    """Validate + clean the Story Architect's output (the Story Bible)."""
    if not isinstance(story, dict):
        raise RuntimeError("script(long): architect returned no story bible")
    p = story.get("protagonist") or {}
    name, desc = str(p.get("name") or "").strip(), str(p.get("description") or "").strip()
    if not (name and desc):
        raise RuntimeError("script(long): story bible has no named protagonist with a description")
    arg = story.get("argument") or {}
    claim = str(arg.get("claim") or "").strip()
    if not claim:
        raise RuntimeError("script(long): story bible has no argument.claim (the verdict)")
    stance = str(arg.get("stance") or "").strip()
    if stance not in _STANCES:
        stance = "dangerously-half-right"
    acts_in = story.get("acts")
    if not isinstance(acts_in, list) or len(acts_in) < 2:
        raise RuntimeError("script(long): story bible needs >= 2 acts")
    acts = []
    for i, a in enumerate(acts_in, 1):
        a = a if isinstance(a, dict) else {}
        ideas = [{"idea": str(x.get("idea") or "").strip(),
                  "mode": (str(x.get("mode") or "").strip() if str(x.get("mode") or "").strip() in _MODES else "tool")}
                 for x in (a.get("ideas") or []) if isinstance(x, dict) and str(x.get("idea") or "").strip()]
        carries = str(a.get("carries") or "none").strip()
        acts.append({
            "title": str(a.get("title") or f"Act {i}").strip(),
            "focus": str(a.get("focus") or "").strip(),
            "role": str(a.get("role") or "").strip(),
            "ideas": ideas,
            "carries": carries if carries in _CARRIES else "none",
        })
    wager = story.get("wager") or {}
    out = str(wager.get("outcome") or "").strip()
    return {
        "protagonist": {"name": name, "description": desc, "wound": str(p.get("wound") or "").strip()},
        "argument": {"stance": stance, "claim": claim},
        "wager": {"book_claim_on_trial": str(wager.get("book_claim_on_trial") or "").strip(),
                  "decision": str(wager.get("decision") or "").strip(),
                  "outcome": out if out in _OUTCOMES else "mixed"},
        "plant": str(story.get("plant") or "").strip(),
        "payoff": str(story.get("payoff") or "").strip(),
        "closing_scene": str(story.get("closing_scene") or "").strip(),
        "opening_move": str(story.get("opening_move") or "").strip(),
        "voice_moves": [str(v).strip() for v in (story.get("voice_moves") or []) if str(v).strip()],
        "acts": acts,
    }
