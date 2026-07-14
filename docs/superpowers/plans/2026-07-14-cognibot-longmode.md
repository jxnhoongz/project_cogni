# Cognibot Long-Mode Rewrite Plan

> Executes the deferred "long-mode Cognibot rewrite" so a ~30-min video follows ONE protagonist across chapters (verdict woven in), matching the short-mode rewrite from Phase 1.

**Goal:** `script.mode: long` produces a chaptered Cognibot deep-dive that follows one invented protagonist across all chapters, with per-beat images and the honest verdict woven through — the 30-minute v1.

**Architecture:** The structure pass invents the protagonist AND plans chapters (returns `{character, chapters}`). Each chapter pass receives that character and writes beats that follow them. `_generate_long` threads the character through and stores it on the doc (same `character` field Phase 2's image stage already consumes). `_SYSTEM`, `_SCENE_RULES`, `_validate`, `_validate_character`, `_scene_record` are unchanged (already Cognibot from Phase 1).

**Tech Stack:** Python (`cogni/script.py`), local `claude` CLI, pytest.

## Global Constraints

- Windows; `.venv\Scripts\python.exe`. Preserve the per-scene schema + the doc `character` field shape (`{"name","description"}`).
- Branch `claude/cognibot-redesign`. Do not touch short mode (`_build_prompt`, `_generate_short`) or other stages.

## File Structure

- `cogni/script.py` — modify `_build_structure_prompt`, `_build_chapter_prompt` (new `character` param), `_generate_long`.
- `tests/test_script.py` — add long-mode prompt tests.

---

### Task 1: Rewrite long mode for the Cognibot character-arc

**Files:**
- Modify: `cogni/script.py`
- Test: `tests/test_script.py`

**Interfaces:**
- `_build_structure_prompt(outline, angle, lo_ch, hi_ch, minutes) -> str` — now invents a protagonist and asks for `{"character": {...}, "chapters": [...]}`.
- `_build_chapter_prompt(outline, angle, character, chapter, idx, total, prior_titles, lo_sc, hi_sc) -> str` — new 3rd param `character: dict|None`; threads the same person + writes beats.
- `_generate_long(cfg, outline, angle) -> (list[dict], {"character": dict|None, "chapters": list[str]})`.

- [ ] **Step 1: Add failing tests** (append to `tests/test_script.py`):

```python
def test_structure_prompt_is_cognibot_character_arc():
    p = script._build_structure_prompt(OUTLINE, "angle", 5, 7, 30)
    assert "Cognibot" in p
    assert "protagonist" in p.lower() or "character" in p.lower()
    assert '"character"' in p and '"chapters"' in p


def test_chapter_prompt_threads_character():
    ch = {"title": "The Trap", "focus": "sets up the problem"}
    p = script._build_chapter_prompt(
        OUTLINE, "angle", {"name": "Dana", "description": "nurse in scrubs, seen from behind"},
        ch, 1, 6, [], 10, 14,
    )
    assert "Dana" in p
    assert "scrubs" in p
    assert "beat" in p.lower()
```

- [ ] **Step 2: Run to confirm fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_script.py -k "structure or chapter" -v`
Expected: FAIL (`_build_chapter_prompt` missing the `character` arg / assertions on prompt text).

- [ ] **Step 3: Replace `_build_structure_prompt`** in `cogni/script.py`:

```python
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
        f"Cognibot's honest take (what it nails, what it skips or oversells). Distinct "
        f"angles, no repeats.\n"
        f"- The FINAL chapter delivers the character's outcome + the earned verdict + who it "
        f"actually helps.\n\n"
        f'Return JSON: {{"character": {{"name": <string>, "description": <one sentence on '
        f'how they look as a recurring silhouette>}}, "chapters": [{{"title": ..., '
        f'"focus": ...}}, ...]}}. title = short chapter title; focus = 1-2 sentences on what '
        f"this chapter covers and its role in the character's arc."
    )
```

- [ ] **Step 4: Replace `_build_chapter_prompt`** in `cogni/script.py` (adds the `character` param):

```python
def _build_chapter_prompt(
    outline: dict[str, Any], angle: str, character: dict[str, str] | None,
    chapter: dict[str, Any], idx: int, total: int, prior_titles: list[str],
    lo_sc: int, hi_sc: int,
) -> str:
    if idx == 1:
        role = ("the COLD OPEN — open on the character's relatable problem as a provocative "
                "question; do NOT state the verdict, no 'in this video' intro")
    elif idx == total:
        role = "the FINAL chapter — the character's outcome, the earned verdict, and who it helps"
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
```

- [ ] **Step 5: Replace `_generate_long`** in `cogni/script.py` (extract + thread the character):

```python
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
```

- [ ] **Step 6: Run tests** — the two new tests plus the existing ones.

Run: `.venv\Scripts\python.exe -m pytest tests/test_script.py -v`
Expected: all PASS (6 total).

- [ ] **Step 7: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): long mode follows one Cognibot protagonist across chapters"
```

---

### Task 2: Switch to long mode + regenerate the 30-min cut (run + review — inline, done by reviewer)

- [ ] Set `config.yaml` `script.mode: long` and `script.long.target_minutes: 30`.
- [ ] `main.py script --force` → review the chaptered Cognibot narration (one protagonist across chapters, verdict woven, ~60-80 beats).
- [ ] `main.py narrate --force` (Brian).
- [ ] `main.py images --force` (~$3; spot-check character consistency across chapters).
- [ ] `main.py assemble --force` → the full ~30-min still cut. Review, then continue to polish (dissolves/music/open-on-HIGH), intro/outro, SEO.

## Self-Review

- Long mode → one protagonist across chapters: Task 1 (structure invents character; chapter prompt threads it; `_generate_long` stores it). ✅
- Character reused by images: same doc `character` field Phase 2 consumes. ✅
- No placeholders; `character` param threaded consistently (structure → `_generate_long` → `_build_chapter_prompt`); short mode untouched. ✅
