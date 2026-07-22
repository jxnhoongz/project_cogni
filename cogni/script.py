"""Stage 2: script — outline.json -> scenes.json.

Turn the outline into a coherent script with a POINT OF VIEW — a verdict, not a
summary — broken into scenes (narration + on_screen_text + image_prompt). Two modes
(config.yaml script.mode):

  - "short": one model pass, min/max_scenes scenes (~4-5 min). Fast, cheap; for tests.
  - "long":  an Architect pass designs a video bible (hook puzzles, promise, argument,
             where the book is wrong, acts), then ONE focused pass per act produces its
             scenes. Keeps each call sharp while reaching a ~30-45 min deep-dive. Scenes
             are concatenated with continuous ids; act titles are recorded on the doc
             (as "chapters") and each scene; the full bible is recorded as "story".

             The VIEWER is the protagonist — second person, no invented characters.
             The earlier design followed a fictional person per book; it tested badly
             (a listener A/B was decisive) and it starved the ideas: book #5 delivered
             7 of 12 key ideas with 58% of runtime on invented story. Only real people
             appear now — usually the author, carried in `recurring_figure`.

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
    "TEACH: a real point of view, a verdict, not a summary. You address the VIEWER "
    "directly as 'you' — the viewer is the protagonist, and you never invent a "
    "fictional character to stand in for them. Your one unfair advantage is that you "
    "hold the whole book at once and know what happened after it was published. "
    "You return only valid JSON."
)

# Shared scene-writing rules, used by the short pass and every chapter pass.
_SCENE_RULES = (
    "- narration: what Cognibot says in this beat. Clear, natural, spoken first person. "
    "Teach through the character's story and give Cognibot's pointed, specific judgement; "
    "never flatly summarize.\n"
    "- on_screen_text: a very short caption for the screen (<= 6 words), or \"\" if none.\n"
    "- image_prompt: describe ONE still image for THIS beat — the single concrete moment "
    "being narrated right now, not the scene's whole idea. Prefer objects, places, and "
    "physical situations over talking heads. People may appear (the author, real historical "
    "figures, or an anonymous everyday body — hands, a commuter, a crowd) as stylized, "
    "faceted LOW-POLY figures; a clear low-poly face is good, never photorealistic. "
    "NEVER render an idea as words, charts, labels, documents or signage — the image model "
    "garbles text. Carry a concept with OBJECTS instead (coin stacks, not a graph). "
    "Do not mention art style (added separately).\n"
    f"- {avoid_clause()}"
)


def _shapes_from_docs(docs: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Story-shapes already used by other books — to force variety.

    `names` matters as much as the rest: the writer defaults HARD to "Marcus" (books 1
    and 3 both got one, and the architect reached for it again once the old name
    blocklist was removed). Read the name from the story bible, falling back to the
    legacy top-level `character` so pre-bible books still count.
    """
    stances, hooks, claims = set(), set(), set()
    for d in docs:
        st = (d or {}).get("story") or {}
        arg = st.get("argument") or {}
        if s := str(arg.get("stance") or "").strip():
            stances.add(s)
        if c := str(arg.get("claim") or "").strip():
            claims.add(c[:120])
        # new-format books carry hook_puzzles; legacy books carry opening_move. Read both
        # so the older five still count toward "don't repeat yourself".
        for h in _as_str_list(st.get("hook_puzzles"))[:1]:
            hooks.add(h[:120])
        if o := str(st.get("opening_move") or "").strip():
            hooks.add(o[:120])
    return {"stances": sorted(stances), "hooks": sorted(hooks), "claims": sorted(claims)}


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
    n_ideas = len(outline["key_ideas"])
    used = ""
    if any(shapes.get(k) for k in ("stances", "hooks", "claims")):
        used = (
            "\nOther videos on this channel already used these — pick DIFFERENT ones:\n"
            f"  - verdict stances used: {', '.join(shapes.get('stances') or []) or 'none'}\n"
            f"  - openings used: {'; '.join(shapes.get('hooks') or []) or 'none'}\n"
            f"  - verdicts already argued: {'; '.join(shapes.get('claims') or []) or 'none'}\n"
        )
    return (
        f"Book: {outline['title']}"
        + (f" by {outline['author']}" if outline.get("author") else "")
        + f"\nThesis: {outline['thesis']}\n\nKey ideas:\n{ideas}\n\n"
        f"Stance to hold (do NOT import a house opinion; make the verdict specific to THIS book):\n{angle}\n\n"
        f"You are Cognibot, ARCHITECTING a ~{minutes}-minute video.\n\n"
        f"FORMAT — this is not negotiable:\n"
        f"- The VIEWER is the protagonist. Second person, throughout. NEVER invent a fictional "
        f"character; do not write 'meet Sarah, a marketing manager'. The only people who appear are "
        f"REAL: the author, real historical figures, and the viewer.\n"
        f"- OPEN with a cascade of concrete, sensory, second-person puzzles the viewer already feels, "
        f"escalating from their own ordinary life to the question this book claims to answer. Each one "
        f"opens a curiosity gap. No scene-setting, no story.\n"
        f"- Then EARN trust with the real story of the book and its author — what actually happened.\n"
        f"- Then make an explicit PROMISE: what you will unpack, and what the viewer will see "
        f"differently afterwards. This is their reason to stay.\n"
        f"- DELIVER THE IDEAS DENSELY. This video must carry ALL {n_ideas} key ideas listed above. "
        f"Every idea gets a CONCRETE ANCHOR — a hard fact, number, object, or piece of history that "
        f"makes it stick. An idea without an anchor is a platitude.\n"
        f"- PUZZLE-FIRST — this is the engine of watchability. Never state an idea and then explain it. "
        f"Every idea ENTERS as a concrete, second-person QUESTION or PARADOX the viewer cannot answer — "
        f"'why does your fridge have a light but your freezer doesn't?' — held open for a beat, THEN paid "
        f"off. The question comes BEFORE the answer, always. For a book with no trivia, the puzzle is a "
        f"TENSION the viewer feels in their own life (e.g. 'why did the man who preached that meaning "
        f"saves you survive by pure luck?'). Give each idea its `puzzle`.\n"
        f"- Near the end, a section on WHERE THE BOOK IS WRONG or what it could not see: research "
        f"that came after it, claims that failed to survive, what the author later conceded. This is "
        f"your unfair advantage — use it.\n"
        f"- The VERDICT is withheld until the end, and it must be earned by the ideas, not asserted.\n"
        f"{used}\n"
        f"Design the whole thing, then output it as JSON:\n"
        f"{{\n"
        f'  "hook_puzzles": [<3-5 short, concrete, SECOND-PERSON puzzles for the cold open, escalating '
        f'from the viewer\'s own life to the book\'s big question. Sensory and specific>],\n'
        f'  "promise": <one sentence: what this video unpacks and what the viewer will see differently>,\n'
        f'  "author_story": <the real, verifiable story of the author and how this book came to exist — '
        f'the parts that are genuinely gripping. Facts only>,\n'
        f'  "recurring_figure": {{"name": <a REAL person who genuinely recurs, usually the author — or '
        f'null if none>, "description": <if named: one sentence of concrete low-poly look — approximate '
        f'age, SKIN TONE, hair colour+length, facial hair, one signature garment. The image model '
        f're-invents anything you leave out>}},\n'
        f'  "argument": {{"stance": <"mostly-right" | "mostly-wrong" | "dangerously-half-right">, '
        f'"claim": <one sentence someone could disagree with, ABOUT THIS BOOK — the earned verdict>}},\n'
        f'  "where_the_book_is_wrong": <what the book could not see or got wrong, concretely — later '
        f'research, a failed replication, an author who recanted, history that overtook it. "" if truly none>,\n'
        f'  "closing_image": <one concrete final image or moment that embodies the verdict>,\n'
        f'  "voice_moves": [<1-2 moves only a bot could make: total recall of the whole text, catching '
        f'the book contradict itself, knowing what was published after it>],\n'
        f'  "acts": [{{"title": <short>, "focus": <1-2 sentences>, "role": <its job in the arc>, '
        f'"ideas": [{{"idea": <which key idea>, "puzzle": <the concrete second-person QUESTION or paradox '
        f'that OPENS this idea, before any answer>, "anchor": <the concrete fact/object/number that makes '
        f'it land>}}], "bridge_out": <one line ending the act: synthesise what just landed, then pose the '
        f'next act as an open question — the cliffhanger that carries the viewer across the seam>, '
        f'"carries": <"hook" | "ideas" | "where-wrong" | "verdict" | "none">}}, ...]\n'
        f"}}\n"
        f"Plan {lo_ch}-{hi_ch} acts. Act 1 carries the hook. Exactly one act carries the verdict (last). "
        f"If there is real material for it, one act carries where-wrong, just before the verdict. "
        f"Order acts so scope escalates — outward objects toward the viewer's own mind — where the "
        f"material allows. Spread ALL {n_ideas} key ideas across the acts — do not drop any."
    )


def _build_act_prompt(outline: dict[str, Any], bible: dict[str, Any], act: dict[str, Any],
                      idx: int, total: int, prior_titles: list[str], lo_sc: int, hi_sc: int) -> str:
    ideas = "; ".join(
        f"{i['idea']}"
        + (f" [OPEN on the puzzle: {i['puzzle']}]" if i.get("puzzle") else "")
        + (f" (anchor: {i['anchor']})" if i.get("anchor") else "")
        for i in act["ideas"]
    ) or "(no new book idea this act)"
    prior = "; ".join(prior_titles) if prior_titles else "(this is the first act)"
    bridge = str(act.get("bridge_out") or "").strip()
    carries = act["carries"]
    extra = ""
    if carries == "hook":
        puzzles = "; ".join(bible["hook_puzzles"])
        extra = (f"\nTHIS act is the COLD OPEN. Start on the puzzles — {puzzles} — in second person, "
                 f"concrete and sensory, escalating. Then the real story of the book and its author: "
                 f"{bible['author_story']}. Close the act on the PROMISE: {bible['promise']}. "
                 f"Give the viewer an explicit reason to stay.")
    elif carries == "where-wrong":
        extra = (f"\nTHIS act is where the book does NOT hold up: {bible['where_the_book_is_wrong']}. "
                 f"Be specific and fair — name what actually happened, and give the author credit where "
                 f"they conceded it. This is the flex only a reader with total recall can make.")
    elif carries == "verdict":
        bits = ["\nTHIS is where it lands."]
        bits.append(f"Deliver the WITHHELD verdict for the first time: \"{bible['argument']['claim']}\".")
        bits.append("Earn it from the ideas already delivered — do not assert it cold.")
        if bible["closing_image"]:
            bits.append(f"End on: {bible['closing_image']} — one concrete image.")
        bits.append("Do NOT end on a 'who this is for' list.")
        extra = " ".join(bits)
    voice = ", ".join(bible["voice_moves"])
    fig = bible.get("recurring_figure") or {}
    fig_line = (f"A real recurring figure appears in this video: {fig['name']} — {fig['description']}. "
                f"Use them only where they genuinely belong.\n" if fig.get("name") else "")
    return (
        f"Book: {outline['title']}\nThesis: {outline['thesis']}\n\n"
        f"You are Cognibot, writing ONE act of a video addressed directly to the VIEWER. "
        f"Acts already written: {prior}.\n{fig_line}\n"
        f"Write ACT {idx} of {total}: \"{act['title']}\". Role in the arc: {act['role'] or '(continue)'}.\n"
        f"Focus: {act['focus']}\nBook ideas this act must deliver: {ideas}.{extra}\n\n"
        f"RULES:\n"
        f"- SECOND PERSON. Talk to the viewer as 'you', constantly and concretely. The viewer is the "
        f"protagonist of this video.\n"
        f"- PUZZLE-FIRST. Open each idea on its puzzle — the concrete second-person question or paradox — "
        f"and make the viewer feel the not-knowing before you resolve it. Never state the idea then "
        f"explain; pose the question, sit in it, THEN pay it off. This is what makes it watchable.\n"
        f"- INVENT NO ONE. No fictional characters, no composite people, no 'imagine a woman named...'. "
        f"Real people only: the author, real historical figures, and the viewer. If you need a human "
        f"body for an example, it is the VIEWER'S ('you walk into...'), not a stranger's.\n"
        f"- Every idea lands on its CONCRETE ANCHOR — a real fact, number, object, or piece of history. "
        f"Explaining is fine; explaining without an anchor is not.\n"
        f"- Do NOT deliver the final verdict early. Only the verdict act judges.\n"
        f"- No 'here's my take on this stretch' summaries, no 'in this video' throat-clearing.\n"
        + (f"- END this act on the bridge — {bridge} — a synthesise-then-open-question hook into what's "
           f"next; do not just stop.\n" if bridge and carries not in ("verdict",) else "")
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
    # `character` is the doc-level recurring-look slot that `images` locks a reference
    # portrait to. It is no longer an invented protagonist — it is a REAL person (usually
    # the author) or None, in which case images simply skips character-locking.
    character = bible["recurring_figure"]
    acts = bible["acts"]
    who = character["name"] if character else "no recurring figure"
    print(f"[script] video bible ready — {who}, {len(acts)} acts, "
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
# What job an act does. Replaces the old invented-story vocabulary (wager/plant/payoff):
# the spine is now the book's own argument, not a fictional person's arc.
#   hook       - the second-person puzzle cascade + the promise
#   ideas      - delivers book ideas, each on a concrete anchor
#   where-wrong- what the book could not see (published after it, or failed to survive)
#   verdict    - the judgement, held until here
_CARRIES = {"hook", "ideas", "where-wrong", "verdict", "none"}


def _as_str_list(v: Any) -> list[str]:
    """Coerce a model-supplied list-of-strings, tolerating a single bare string."""
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    return [str(x).strip() for x in v if str(x).strip()]


def _validate_story(story: dict[str, Any]) -> dict[str, Any]:
    """Validate + clean the Story Architect's output (the Story Bible)."""
    if not isinstance(story, dict):
        raise RuntimeError("script(long): architect returned no story bible")
    puzzles = _as_str_list(story.get("hook_puzzles"))
    if not puzzles:
        raise RuntimeError("script(long): bible has no hook_puzzles (the cold open IS the hook)")
    promise = str(story.get("promise") or "").strip()
    if not promise:
        raise RuntimeError("script(long): bible has no promise (the viewer's reason to stay)")
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
        ideas = []
        for x in (a.get("ideas") or []):
            # tolerate the shorthand `"ideas": ["compounding", ...]` — dropping bare
            # strings silently stripped the book's ideas out of the act prompt.
            if isinstance(x, str):
                x = {"idea": x}
            if not isinstance(x, dict) or not str(x.get("idea") or "").strip():
                continue
            ideas.append({"idea": str(x["idea"]).strip(),
                          "puzzle": str(x.get("puzzle") or "").strip(),
                          "anchor": str(x.get("anchor") or "").strip()})
        carries = str(a.get("carries") or "none").strip()
        acts.append({
            "title": str(a.get("title") or f"Act {i}").strip(),
            "focus": str(a.get("focus") or "").strip(),
            "role": str(a.get("role") or "").strip(),
            "ideas": ideas,
            "bridge_out": str(a.get("bridge_out") or "").strip(),
            "carries": carries if carries in _CARRIES else "none",
        })

    # INVARIANTS: only the verdict act judges, and only the hook act opens. If the
    # architect phrased `carries` off-vocabulary, everything coerced to "none" above and
    # NO act would ever judge — a full-length script with no verdict, silently. Pin them.
    if not any(a["carries"] == "verdict" for a in acts):
        acts[-1]["carries"] = "verdict"
    if not any(a["carries"] == "hook" for a in acts):
        acts[0]["carries"] = "hook"
    # where-wrong is the payoff flex, but only if the book actually gives us material.
    where_wrong = str(story.get("where_the_book_is_wrong") or "").strip()
    if where_wrong and not any(a["carries"] == "where-wrong" for a in acts):
        late = next((a for a in reversed(acts[1:-1]) if a["carries"] == "none"), None)
        if late is not None:
            late["carries"] = "where-wrong"

    fig_in = story.get("recurring_figure") or {}
    fig_name = str(fig_in.get("name") or "").strip()
    fig_desc = str(fig_in.get("description") or "").strip()
    # Both halves or neither: a name with no description gives the image model nothing to
    # lock onto, which is exactly how a protagonist changed race mid-video once.
    figure = {"name": fig_name, "description": fig_desc} if (fig_name and fig_desc) else None

    return {
        "hook_puzzles": puzzles,
        "promise": promise,
        "author_story": str(story.get("author_story") or "").strip(),
        "recurring_figure": figure,
        "argument": {"stance": stance, "claim": claim},
        "where_the_book_is_wrong": where_wrong,
        "closing_image": str(story.get("closing_image") or "").strip(),
        # a bare string is iterable: without this, "total recall" became 12 one-character
        # "voice moves" injected into every act prompt.
        "voice_moves": _as_str_list(story.get("voice_moves")),
        "acts": acts,
    }
