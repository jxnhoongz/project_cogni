# Cognibot Script Story-Architect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `cogni/script.py` (long mode) so "test, don't illustrate" and "one book, one earned argument" are the default architecture — a Story Architect pass emits a Story Bible, and the Act Writer dramatizes it — plus a within-script crutch checker.

**Architecture:** Two model passes (same count as today). The Architect pass replaces the structure pass and returns a Story Bible (protagonist+wound, one book-specific argument, a central wager the book can lose, plant→payoff, closing scene, act-map). The Act Writer (rewritten chapter pass) dramatizes each act from the bible. The bible is stored on `scenes.json` as `doc["story"]`; the per-scene schema is unchanged.

**Tech Stack:** Python 3, pytest 9.1.1, the existing `cogni.llm.call_stage` LLM wrapper. No new dependencies.

## Global Constraints

- Per-scene `scenes.json` schema is UNCHANGED (`narration`, `on_screen_text`, `image_prompt`, `chapter`, plus the fields `_scene_record` already sets). Downstream stages must keep working untouched.
- Only `doc["story"]` is added to the document.
- LLM calls go through `call_stage(cfg, "script", prompt, system=_SYSTEM, json_out=True)` — never call a provider directly.
- Long mode only. Short mode (`script.mode: short`) is left exactly as-is.
- Tests are pure-function content/dict assertions (see `tests/test_script.py`); do NOT hit a live LLM in tests — monkeypatch `call_stage` where a pass must be exercised.
- Run tests with `.venv/Scripts/python.exe -m pytest`.

---

## The Story Bible shape (shared contract — every task refers to this)

```python
bible = {
    "protagonist": {"name": str, "description": str, "wound": str},
    "argument": {"stance": str, "claim": str},        # stance in {mostly-right, mostly-wrong, dangerously-half-right}
    "wager": {"book_claim_on_trial": str, "decision": str, "outcome": str},  # outcome in {book-wins, book-loses, mixed}
    "plant": str,
    "payoff": str,
    "closing_scene": str,
    "opening_move": str,
    "voice_moves": [str, ...],
    "acts": [
        {"title": str, "focus": str, "role": str,
         "ideas": [{"idea": str, "mode": str}],       # mode in {tool, obstacle, failure, discovery}
         "carries": str},                              # carries in {wager, plant, payoff, none}
        ...
    ],
}
```

---

### Task 1: Story Bible validator

**Files:**
- Modify: `cogni/script.py` (add `_validate_story`, near `_validate_character`)
- Test: `tests/test_script.py`

**Interfaces:**
- Produces: `_validate_story(data: dict) -> dict` — returns a cleaned bible (shape above). Raises `RuntimeError` if `protagonist.name`/`protagonist.description`/`argument.claim` are missing or `acts` has fewer than 2 entries. Optional fields default: `wound=""`, `voice_moves=[]`, `plant=""`, `payoff=""`, `closing_scene=""`, `opening_move=""`; each act's `carries` defaults to `"none"`, `ideas` to `[]`.

- [ ] **Step 1: Write the failing tests**

```python
# add to tests/test_script.py
def test_validate_story_ok():
    data = {"story": {
        "protagonist": {"name": "Theo", "description": "tired man in teal", "wound": "watched his dad retire broke"},
        "argument": {"stance": "dangerously-half-right", "claim": "Housel's patience is a luxury good"},
        "wager": {"book_claim_on_trial": "just be patient", "decision": "bet the emergency fund on a tip", "outcome": "book-loses"},
        "plant": "the aquarium trip", "payoff": "his kid ignores the watch",
        "closing_scene": "Theo at the aquarium", "opening_move": "envy", "voice_moves": ["total recall"],
        "acts": [
            {"title": "A", "focus": "f", "role": "cold open", "ideas": [{"idea": "compounding", "mode": "obstacle"}], "carries": "none"},
            {"title": "B", "focus": "g", "role": "final", "ideas": [], "carries": "payoff"},
        ],
    }}
    b = script._validate_story(data["story"])
    assert b["protagonist"]["name"] == "Theo"
    assert b["argument"]["stance"] == "dangerously-half-right"
    assert b["acts"][1]["carries"] == "payoff"

def test_validate_story_defaults_optionals():
    b = script._validate_story({
        "protagonist": {"name": "X", "description": "d"},
        "argument": {"claim": "c"},
        "acts": [{"title": "1"}, {"title": "2"}],
    })
    assert b["protagonist"]["wound"] == ""
    assert b["voice_moves"] == []
    assert b["acts"][0]["carries"] == "none" and b["acts"][0]["ideas"] == []

def test_validate_story_rejects_missing_argument_and_thin_acts():
    import pytest
    with pytest.raises(RuntimeError):
        script._validate_story({"protagonist": {"name": "X", "description": "d"}, "acts": [{"title": "1"}, {"title": "2"}]})
    with pytest.raises(RuntimeError):
        script._validate_story({"protagonist": {"name": "X", "description": "d"}, "argument": {"claim": "c"}, "acts": [{"title": "1"}]})
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k validate_story -v`
Expected: FAIL — `AttributeError: module 'cogni.script' has no attribute '_validate_story'`

- [ ] **Step 3: Implement `_validate_story`**

```python
# in cogni/script.py
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
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k validate_story -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): Story Bible validator (_validate_story)"
```

---

### Task 2: Prior story-shapes collector (cross-video variety)

**Files:**
- Modify: `cogni/script.py` (add `_shapes_from_docs` + `_prior_story_shapes`, near `_prior_protagonists`)
- Test: `tests/test_script.py`

**Interfaces:**
- Produces: `_shapes_from_docs(docs: list[dict]) -> dict` — pure; returns `{"stances": [..], "openings": [..], "wagers": [..]}` (deduped, sorted) from each doc's `doc["story"]`. Tolerates docs with no `story`.
- Produces: `_prior_story_shapes(cfg) -> dict` — filesystem wrapper (same rglob pattern as `_prior_protagonists`), returns the same dict for all OTHER books. Not unit-tested (mirrors `_prior_protagonists`, which isn't either).

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_script.py
def test_shapes_from_docs_collects_and_dedupes():
    docs = [
        {"story": {"argument": {"stance": "mostly-right"}, "opening_move": "envy",
                   "wager": {"book_claim_on_trial": "just be patient"}}},
        {"story": {"argument": {"stance": "mostly-right"}, "opening_move": "crisis",
                   "wager": {"book_claim_on_trial": "cut the lattes"}}},
        {"scenes": []},  # old book, no story — tolerated
    ]
    s = script._shapes_from_docs(docs)
    assert s["stances"] == ["mostly-right"]                 # deduped
    assert set(s["openings"]) == {"crisis", "envy"}
    assert "just be patient" in s["wagers"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k shapes_from_docs -v`
Expected: FAIL — no attribute `_shapes_from_docs`

- [ ] **Step 3: Implement**

```python
# in cogni/script.py
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k shapes_from_docs -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): collect prior story-shapes for cross-video variety"
```

---

### Task 3: Story Architect prompt builder

**Files:**
- Modify: `cogni/script.py` (add `_build_architect_prompt`; it replaces `_build_structure_prompt`, which is deleted in Task 5)
- Test: `tests/test_script.py`

**Interfaces:**
- Produces: `_build_architect_prompt(outline: dict, angle: str, lo_ch: int, hi_ch: int, minutes: int, shapes: dict) -> str`

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_script.py
def test_architect_prompt_demands_bible():
    p = script._build_architect_prompt(
        OUTLINE, "angle", 5, 7, 30,
        {"stances": ["mostly-right"], "openings": ["envy"], "wagers": ["just be patient"]},
    )
    assert "Cognibot" in p
    for key in ('"argument"', '"wager"', '"plant"', '"payoff"', '"closing_scene"', '"acts"', '"wound"'):
        assert key in p, key
    assert "test" in p.lower() and "illustrat" in p.lower()      # test, don't illustrate
    assert "mostly-right" in p and "envy" in p                    # variety: prior shapes fed in
    assert "lose" in p.lower()                                    # the book can lose the wager
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k architect_prompt -v`
Expected: FAIL — no attribute `_build_architect_prompt`

- [ ] **Step 3: Implement (draft prompt — tuned in Task 8 validation)**

```python
# in cogni/script.py
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k architect_prompt -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): Story Architect prompt (bible + test-don't-illustrate)"
```

---

### Task 4: Act Writer prompt (rewrite of the chapter pass)

**Files:**
- Modify: `cogni/script.py` (add `_build_act_prompt`; replaces `_build_chapter_prompt`, deleted in Task 5)
- Test: `tests/test_script.py`

**Interfaces:**
- Consumes: a `bible` dict (Task 1 shape) and one `act` element from `bible["acts"]`.
- Produces: `_build_act_prompt(outline: dict, bible: dict, act: dict, idx: int, total: int, prior_titles: list[str], lo_sc: int, hi_sc: int) -> str`

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_script.py
BIBLE = {
    "protagonist": {"name": "Theo", "description": "tired man in a teal shirt", "wound": "watched his dad retire broke"},
    "argument": {"stance": "dangerously-half-right", "claim": "patience is a luxury good"},
    "wager": {"book_claim_on_trial": "just be patient", "decision": "bet the emergency fund", "outcome": "book-loses"},
    "plant": "the aquarium trip", "payoff": "his kid ignores the watch", "closing_scene": "Theo at the aquarium",
    "opening_move": "crisis", "voice_moves": ["total recall"],
    "acts": [{"title": "The Bet", "focus": "he risks the fund", "role": "the wager",
              "ideas": [{"idea": "margin of safety", "mode": "failure"}], "carries": "wager"}],
}

def test_act_prompt_dramatizes_and_carries_wager():
    p = script._build_act_prompt(OUTLINE, BIBLE, BIBLE["acts"][0], 3, 6, ["Cold Open"], 10, 14)
    assert "Theo" in p and "teal shirt" in p            # threads protagonist
    assert "watched his dad retire broke" in p          # threads the wound
    assert "margin of safety" in p                       # the act's idea
    assert "dramatize" in p.lower() or "do not explain" in p.lower()
    assert "wager" in p.lower() and "lose" in p.lower()  # this act carries the wager; book can lose
    assert "honest" not in p.lower()                     # we don't tell it to be "honest" (the crutch)

def test_act_prompt_final_pays_off_verdict():
    final = dict(BIBLE["acts"][0]); final["carries"] = "payoff"; final["role"] = "final"
    p = script._build_act_prompt(OUTLINE, BIBLE, final, 6, 6, ["a", "b"], 10, 14)
    assert "patience is a luxury good" in p              # the withheld argument lands here
    assert "aquarium" in p.lower()                        # the closing scene
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k act_prompt -v`
Expected: FAIL — no attribute `_build_act_prompt`

- [ ] **Step 3a: Clean `_SCENE_RULES` (remove the "honest" crutch it injects)**

The act prompt appends `_SCENE_RULES`, whose first bullet currently says *"give your honest take on the book; never flatly summarize"* — that word is exactly the crutch we're removing, and it would fail the "honest not in prompt" test. Change that bullet to:

```python
    "- narration: what Cognibot says in this beat. Clear, natural, spoken first person. "
    "Teach through the character's story and give Cognibot's pointed, specific judgement; "
    "never flatly summarize.\n"
```

(Short mode's `_build_prompt` shares `_SCENE_RULES`; this change is harmless there. `_build_prompt` keeps its own "JUDGE the book honestly" wording, so `test_build_prompt_is_cognibot_story` still passes on "judge".)

- [ ] **Step 3b: Implement `_build_act_prompt` (draft prompt — tuned in Task 8)**

```python
# in cogni/script.py
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k act_prompt -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): Act Writer prompt (dramatize from the bible)"
```

---

### Task 5: Wire the passes + store the bible on the doc

**Files:**
- Modify: `cogni/script.py` — rewrite `_generate_long`; delete `_build_structure_prompt` and `_build_chapter_prompt` (replaced); `script()` already spreads `extra` into the doc, so `story` flows in automatically.
- Test: `tests/test_script.py`

**Interfaces:**
- Consumes: `_build_architect_prompt`, `_validate_story`, `_prior_story_shapes`, `_build_act_prompt`, `_validate` (existing), `_scene_record` (existing).
- Produces: `_generate_long(cfg, outline, angle) -> (scenes: list[dict], extra: dict)` where `extra = {"character": {...}, "chapters": [titles], "story": bible}`.

- [ ] **Step 1: Write the failing test** (monkeypatch `call_stage` — no live LLM)

```python
# add to tests/test_script.py
def test_generate_long_wires_architect_then_acts(monkeypatch):
    calls = {"n": 0}
    def fake_call_stage(cfg, stage, prompt, **kw):
        calls["n"] += 1
        if "ARCHITECTING" in prompt:                       # the architect pass
            return {"protagonist": {"name": "Theo", "description": "teal shirt guy"},
                    "argument": {"stance": "mostly-wrong", "claim": "the book oversells patience"},
                    "wager": {"book_claim_on_trial": "be patient", "decision": "bet", "outcome": "book-loses"},
                    "acts": [{"title": "Cold Open", "carries": "none"}, {"title": "The Bet", "carries": "wager"}]}
        return {"scenes": [{"narration": "n", "on_screen_text": "", "image_prompt": "i"}]}
    monkeypatch.setattr(script, "call_stage", fake_call_stage)
    monkeypatch.setattr(script, "_prior_story_shapes", lambda cfg: {"stances": [], "openings": [], "wagers": []})
    cfg = {"script": {"long": {"min_chapters": 2, "max_chapters": 2,
                               "min_scenes_per_chapter": 1, "max_scenes_per_chapter": 1, "target_minutes": 20}}}
    scenes, extra = script._generate_long(cfg, OUTLINE, "angle")
    assert calls["n"] == 3                                  # 1 architect + 2 acts
    assert extra["story"]["argument"]["claim"] == "the book oversells patience"
    assert extra["chapters"] == ["Cold Open", "The Bet"]
    assert scenes[0]["chapter"] == "Cold Open" and scenes[1]["chapter"] == "The Bet"
    assert scenes[0]["id"] == 1 and scenes[1]["id"] == 2
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -k generate_long -v`
Expected: FAIL (current `_generate_long` calls the old structure prompt / lacks `story` in extra)

- [ ] **Step 3: Rewrite `_generate_long`**

```python
# replace the body of _generate_long in cogni/script.py
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
```

Then delete `_build_structure_prompt`, `_build_chapter_prompt`, and `_validate_chapters` (now unused). Keep `_prior_protagonists` only if nothing else references it; otherwise delete it too (its variety job is now inside `_prior_story_shapes` / the architect prompt).

- [ ] **Step 4: Run the full script test file**

Run: `.venv/Scripts/python.exe -m pytest tests/test_script.py -v`
Expected: PASS. Two old tests will now fail because the functions they cover were deleted — `test_structure_prompt_is_cognibot_character_arc` and `test_chapter_prompt_threads_character`. Delete those two tests (their replacements are `test_architect_prompt_*` and `test_act_prompt_*`). Re-run: all PASS.

- [ ] **Step 5: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): wire Architect->Act passes, store bible on doc; drop old structure/chapter passes"
```

---

### Task 6: Neutralize the prescriptive `angle` config

**Files:**
- Modify: `config.yaml` (the `script.angle` value)

**Interfaces:** none (config text only).

- [ ] **Step 1: Read the current value**

Run: `.venv/Scripts/python.exe -c "import yaml;print(yaml.safe_load(open('config.yaml',encoding='utf-8'))['script']['angle'])"`
Note what it currently says.

- [ ] **Step 2: Replace the `angle:` block** so it states a stance-agnostic demand, not a house take. New value:

```yaml
  angle: >-
    Reach an honest, book-specific verdict — the one thing that most survives scrutiny and the
    one that least does, decided by THIS book's own material. Do not import a recurring house
    opinion (e.g. a standing "it ignores privilege" line); let each book earn its own judgement.
```

- [ ] **Step 3: Verify it loads**

Run: `.venv/Scripts/python.exe -c "import yaml;print('ok' if yaml.safe_load(open('config.yaml',encoding='utf-8'))['script']['angle'] else 'empty')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add config.yaml
git commit -m "chore(config): neutralize script.angle (verdict comes from the architect)"
```

---

### Task 7: Within-script crutch + skeleton checker

**Files:**
- Create: `scripts/check_crutches.py`
- Create: `tests/test_check_crutches.py`

**Interfaces:**
- Produces: `find_crutches(scenes: list[dict], honest_max: int = 3) -> dict` — pure. Returns `{"honest": [(scene_id, count)...] , "skeleton": [(scene_id, phrase)...]}`. Flags total "honest/honestly" over `honest_max` (reports the offending scenes), and any scene whose narration matches a skeleton phrase.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_check_crutches.py
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "check_crutches", pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check_crutches.py")
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)

def _sc(i, n): return {"id": i, "narration": n}

def test_flags_honest_overuse():
    scenes = [_sc(i, "honest take here") for i in range(1, 6)]   # 5 "honest"
    out = cc.find_crutches(scenes, honest_max=3)
    assert sum(c for _, c in out["honest"]) >= 5
    assert out["honest"]                                          # non-empty -> flagged

def test_ignores_honest_under_threshold():
    out = cc.find_crutches([_sc(1, "an honest look"), _sc(2, "nothing here")], honest_max=3)
    assert out["honest"] == []

def test_flags_skeleton_phrases():
    scenes = [_sc(1, "here's my honest take on this"), _sc(2, "five years later, he was fine"),
              _sc(3, "so who is this book for")]
    out = cc.find_crutches(scenes, honest_max=99)                # isolate skeleton detection
    hit = {sid for sid, _ in out["skeleton"]}
    assert hit == {1, 2, 3}
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_check_crutches.py -v`
Expected: FAIL — file/module not found

- [ ] **Step 3: Implement `scripts/check_crutches.py`**

```python
"""Flag WITHIN-script crutches the reviews called out: the word "honest" overused, and
fixed-skeleton phrases ("here's my honest take", "X years later", "who this is for", "in
this video"). Cross-BOOK reuse is check_tics.py; mispronunciations are check_pronunciation.py.

Run after `script`, before `narrate`. Free, text-only.

Usage:  python scripts/check_crutches.py [--honest-max 3]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

_HONEST = re.compile(r"\bhonest(ly)?\b", re.I)
_SKELETON = [
    re.compile(r"\bhere'?s my (honest )?(take|gripe|read|flag)\b", re.I),
    re.compile(r"\b(in this video|what this book (really )?wants)\b", re.I),
    re.compile(r"\bwho (this|it|the book) (is|really is) (for|not for)\b|\bwho should (skip|read)\b", re.I),
    re.compile(r"\b(a year|two years|three years|five years|six months|months|years) (later|after)\b", re.I),
]


def find_crutches(scenes: list[dict], honest_max: int = 3) -> dict:
    honest_hits, total = [], 0
    skeleton = []
    for s in scenes:
        n = s.get("narration") or ""
        c = len(_HONEST.findall(n))
        if c:
            honest_hits.append((s["id"], c)); total += c
        for pat in _SKELETON:
            if pat.search(n):
                skeleton.append((s["id"], pat.search(n).group(0))); break
    return {"honest": honest_hits if total > honest_max else [], "skeleton": skeleton}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--honest-max", type=int, default=3)
    a = ap.parse_args()
    slug = (REPO / ".active_project").read_text(encoding="utf-8").strip()
    scenes = json.loads((REPO / "projects" / slug / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    out = find_crutches(scenes, a.honest_max)
    if not out["honest"] and not out["skeleton"]:
        print(f"[crutches] {slug}: PASS — no 'honest' overuse or skeleton phrases.")
        return
    if out["honest"]:
        tot = sum(c for _, c in out["honest"])
        print(f"[crutches] 'honest/honestly' used {tot}x (max {a.honest_max}) — cut most; be incisive, don't announce it:")
        for sid, c in out["honest"]:
            print(f"  scene {sid:>3}  x{c}")
    if out["skeleton"]:
        print(f"[crutches] {len(out['skeleton'])} skeleton phrase(s) — vary these so episodes don't feel identical:")
        for sid, ph in out["skeleton"]:
            print(f'  scene {sid:>3}  "{ph}"')
    print("\n[crutches] Rewrite those beats in scenes.json, then re-run.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_check_crutches.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/check_crutches.py tests/test_check_crutches.py
git commit -m "feat(scripts): check_crutches — flag 'honest' overuse + skeleton phrases"
```

---

### Task 8: Validation — regenerate a real script and judge it (observational)

**Files:**
- Modify (regenerated): `projects/the-psychology-of-money/scenes.json` (back it up first)

This task has NO pytest — it verifies the whole change end-to-end by producing a real script and checking it against the reviews' complaints. LLM `script` calls use the Claude subscription (not per-token), so this is effectively free.

- [ ] **Step 1: Run the full unit suite first**

Run: `.venv/Scripts/python.exe -m pytest tests/ -q`
Expected: all PASS.

- [ ] **Step 2: Back up the current WIP script + set the active project**

```bash
cp projects/the-psychology-of-money/scenes.json projects/the-psychology-of-money/_scenes_pre_architect.json
echo "the-psychology-of-money" > .active_project
```

- [ ] **Step 3: Regenerate the script with the new system**

Run: `.venv/Scripts/python.exe main.py script --force`
Expected: logs `story bible ready — <name>, N acts, stance=...`, then `act k/N`. Writes `scenes.json`.

- [ ] **Step 4: Inspect the bible + run the crutch check**

Run:
```bash
.venv/Scripts/python.exe -c "import json;d=json.load(open('projects/the-psychology-of-money/scenes.json',encoding='utf-8'));s=d['story'];print('STANCE',s['argument']['stance']);print('CLAIM',s['argument']['claim']);print('WAGER',s['wager']);print('ACTS',[a['title'] for a in s['acts']])"
.venv/Scripts/python.exe scripts/check_crutches.py
.venv/Scripts/python.exe scripts/check_tics.py
```

- [ ] **Step 5: Judge against the reviews' checklist** (read `scenes.json` narration + `_scenes_pre_architect.json` side by side). Acceptance — the new script must satisfy ALL:
  - `argument.claim` is book-specific and NOT the "ignores privilege" default; the verdict lands only in the final act.
  - `wager.outcome` is `book-loses` or `mixed`, and that loss is actually dramatized in the wager act.
  - Opening move differs from the other three books; no "capable guy + flashy rival + five-years-later" repeat.
  - Middle acts show discovery/failure, not narrator lecture on the framework.
  - `check_crutches` and `check_tics` PASS (or only trivially flag).
  - Ends on the `closing_scene`, not a "who it's for" list.

  If any fail, tune `_build_architect_prompt` (highest leverage) or `_build_act_prompt`, re-run Step 3, re-judge. Do NOT proceed to narrate/images.

- [ ] **Step 6: Commit the regenerated script once it passes**

```bash
git add projects/the-psychology-of-money/scenes.json
git commit -m "content: regenerate Psychology of Money script with the Story Architect"
```

---

### Task 9: Update the runbook

**Files:**
- Modify: `docs/LOOP.md` (the production runbook)

- [ ] **Step 1:** In the pre-`narrate` checks section (next to `check_tics` / `check_pronunciation`), add a line: run `python scripts/check_crutches.py` and rewrite flagged beats.
- [ ] **Step 2:** Add a short note that long-mode `script` now runs a Story Architect pass first (emits `doc["story"]`, the bible) and that the verdict is designed there, not in config `angle`.
- [ ] **Step 3: Commit**

```bash
git add docs/LOOP.md
git commit -m "docs(loop): add check_crutches + Story Architect note"
```

---

## Self-Review

**Spec coverage:** Architect pass → Task 3+5. Story Bible fields → Task 1 (validator) + Task 3 (prompt). Act Writer rewrite → Task 4+5. Cross-video variety → Task 2 + Task 3. Tic automation → Task 7. Config neutralize → Task 6. Schema compat (bible on doc, downstream untouched) → Task 5. Validation on Psychology of Money → Task 8. Runbook → Task 9. No gaps.

**Placeholder scan:** No TBD/TODO; every code step shows full code; the two prompt bodies are real drafts explicitly flagged for tuning in Task 8 (not placeholders).

**Type consistency:** `_validate_story` returns the bible shape used by `_build_act_prompt` and `_generate_long`; `_shapes_from_docs` returns `{stances,openings,wagers}` consumed by `_build_architect_prompt`; `_generate_long` returns `extra` with `story`/`chapters`/`character` matching what `script()` spreads into the doc. Act `carries`/`ideas.mode` vocab is consistent across Tasks 1/3/4.
