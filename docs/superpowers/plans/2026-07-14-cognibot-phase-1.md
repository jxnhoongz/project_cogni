# Cognibot Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the narrator Cognibot — teaching a book's lessons/verdicts through one relatable protagonist's story, in Brian's voice, with Riso-styled subtitles — and remove the stale pre-pivot skills, so the new direction can be heard/seen cheaply before beat-sync (Phase 2) and modes (Phase 3).

**Architecture:** Rewrite the `script` stage's prompt so one LLM pass invents a protagonist and writes a story-arc script (verdict woven in) at the existing per-scene schema. Change one config line for the voice. Refactor `assemble`'s inline subtitle style into a config-driven helper and give it a Riso palette. Delete six dead skills. Validate by regenerating the Rich Dad short script + narration + a single subtitle-preview frame.

**Tech Stack:** Python 3 (`cogni/` package), the local `claude` CLI (via `call_stage`), edge-tts, ffmpeg/ffprobe, pytest (dev only).

## Global Constraints

- Windows host: run Python as `.venv\Scripts\python.exe`; Bash tool is git-bash, PowerShell is primary. Fail loudly on missing files/keys.
- Preserve the per-scene `scenes.json` schema (`_scene_record`) — downstream stages (visuals/review/narrate/images/assemble) must keep working unchanged.
- Do not touch `ingest`, the image provider, or the Risograph STYLE token (`docs/STYLE.md`).
- Narrator voice: `en-US-BrianMultilingualNeural`.
- Subtitle palette: cream text `#F1EDE4`, dark-teal box `#14332E`.
- No new runtime dependencies; `pytest` is dev-only.
- Long mode (`script.mode: long`) is out of scope for Phase 1 (config is `short`); do not break it, but its full Cognibot rewrite is Phase 2/3.

## File Structure

- `.claude/skills/{asset-librarian,book-catalog-manager,copyright-compliance-checker,midform-script-generator,script-quality-checker,video-renderer}/` — **delete** (dead pre-pivot skills).
- `cogni/script.py` — **modify**: Cognibot persona system prompt; short-mode prompt writes a protagonist + story arc; add `_validate_character`; doc gets a `character` field.
- `cogni/assemble.py` — **modify**: extract subtitle style into `_ass_color()` + `_subtitle_style(cfg)`; use Riso palette.
- `config.yaml` — **modify**: `tts.voice` → Brian; add `video.subtitle` style block.
- `tests/test_script.py` — **create**: unit tests for the prompt builder + validators.
- `tests/test_assemble_subtitles.py` — **create**: unit tests for the subtitle-style helpers.

---

### Task 1: Delete the six pre-pivot skills

**Files:**
- Delete: `.claude/skills/asset-librarian/`, `.claude/skills/book-catalog-manager/`, `.claude/skills/copyright-compliance-checker/`, `.claude/skills/midform-script-generator/`, `.claude/skills/script-quality-checker/`, `.claude/skills/video-renderer/`

**Interfaces:** none (removes agent-facing skills only; no code imports them).

- [ ] **Step 1: Remove the six skill folders**

```bash
cd /d/projects/project_cogni
git rm -r ".claude/skills/asset-librarian" ".claude/skills/book-catalog-manager" \
  ".claude/skills/copyright-compliance-checker" ".claude/skills/midform-script-generator" \
  ".claude/skills/script-quality-checker" ".claude/skills/video-renderer"
```

- [ ] **Step 2: Verify only current skills remain**

Run: `ls .claude/skills`
Expected: exactly `cogni-animate` and `irpe` remain.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove stale pre-pivot skills (cognilab/shorts era) to stop agent hallucination"
```

---

### Task 2: Rewrite `script.py` — Cognibot character-story narration (short mode)

**Files:**
- Modify: `cogni/script.py` (the `_SYSTEM`, `_SCENE_RULES`, `_build_prompt`, `_generate_short` symbols; add `_validate_character`)
- Test: `tests/test_script.py`

**Interfaces:**
- Consumes: `outline.json` dict (`title`, `author?`, `thesis`, `key_ideas[]`), `cfg["script"]` (`min_scenes`, `max_scenes`, `angle`).
- Produces: `script()` writes `scenes.json` with a new top-level `character` field (`{"name": str, "description": str}` or `null`) plus the unchanged per-scene records. `_validate_character(data: dict) -> dict | None`. `_build_prompt(outline, angle, lo, hi) -> str` (now Cognibot/story framing). `_generate_short(cfg, outline, angle) -> tuple[list[dict], dict]` where the dict extra is `{"character": <char|None>}`.

- [ ] **Step 1: Ensure pytest is available**

Run: `.venv\Scripts\python.exe -m pip install -q pytest`
Expected: completes (installed or already present).

- [ ] **Step 2: Write failing tests for the new prompt + character validator**

Create `tests/test_script.py`:

```python
from cogni import script

OUTLINE = {
    "title": "Rich Dad Poor Dad",
    "author": "Robert Kiyosaki",
    "thesis": "Financial literacy beats income.",
    "key_ideas": [{"title": "Assets vs liabilities", "summary": "Assets feed you."}],
}


def test_build_prompt_is_cognibot_story():
    p = script._build_prompt(OUTLINE, "an honest angle", 8, 14)
    assert "Cognibot" in p
    assert "character" in p.lower()
    assert "verdict" in p.lower() or "judge" in p.lower()
    assert '"character"' in p  # asks the model to return the character object


def test_validate_character_ok():
    data = {"character": {"name": "Ana", "description": "a tired silhouette in a suit"},
            "scenes": []}
    assert script._validate_character(data) == {
        "name": "Ana", "description": "a tired silhouette in a suit"}


def test_validate_character_missing_is_tolerated():
    assert script._validate_character({"scenes": []}) is None
    assert script._validate_character({"character": {"name": ""}}) is None


def test_validate_scenes_still_works():
    data = {"scenes": [{"narration": "n", "on_screen_text": "o", "image_prompt": "i"}]}
    got = script._validate(data)
    assert got[0] == {"narration": "n", "on_screen_text": "o", "image_prompt": "i"}
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_script.py -v`
Expected: `test_build_prompt_is_cognibot_story` and `test_validate_character_*` FAIL (`AttributeError: _validate_character` / assertion on prompt text); `test_validate_scenes_still_works` PASSES.

- [ ] **Step 4: Update `_SYSTEM` and `_SCENE_RULES`**

In `cogni/script.py`, replace `_SYSTEM`:

```python
_SYSTEM = (
    "You are Cognibot, narrator of a channel that reads books so lazy humans don't "
    "have to. You speak clear, natural, everyday English — never broken robot-speak "
    "(that lives only on the channel banner). You are blunt, a little funny, and you "
    "TEACH: an honest point of view, a verdict, not a summary. You teach a book's ideas "
    "by telling the story of one relatable person it applies to, and you judge the book "
    "as you go. You return only valid JSON."
)
```

Replace `_SCENE_RULES`:

```python
_SCENE_RULES = (
    "- narration: what Cognibot says in this beat. Clear, natural, spoken first person. "
    "Teach through the character's story and give your honest take on the book; never "
    "flatly summarize.\n"
    "- on_screen_text: a very short caption for the screen (<= 6 words), or \"\" if none.\n"
    "- image_prompt: describe ONE still image for THIS beat — the single concrete moment "
    "being narrated right now, not the scene's whole idea. IMPORTANT: no realistic human "
    "faces or hands; favor silhouettes, objects, symbolic imagery, or figures seen from "
    "behind or far away. When the recurring protagonist appears, describe them as the "
    "SAME silhouetted figure for continuity. Do not mention art style (added separately)."
)
```

- [ ] **Step 5: Rewrite the short-mode `_build_prompt`**

Replace `_build_prompt` in `cogni/script.py`:

```python
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
        f'how they look as a recurring silhouette>}}, "scenes": [ {{"narration": ..., '
        f'"on_screen_text": ..., "image_prompt": ...}}, ... ]}} with between {lo} and {hi} '
        f"scenes. Each scene is ONE beat: 1-3 sentences of narration and an image for that "
        f"single moment.\n"
        f"{_SCENE_RULES}"
    )
```

- [ ] **Step 6: Add `_validate_character` and thread it through `_generate_short`**

Add near `_validate` in `cogni/script.py`:

```python
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
```

Replace `_generate_short` so it returns the character in the extra dict:

```python
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
```

(The `character` flows into `doc` via the existing `**extra` spread in `script()`, so no change there.)

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_script.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add cogni/script.py tests/test_script.py
git commit -m "feat(script): Cognibot narration — teach via one protagonist's story (short mode)"
```

---

### Task 3: Riso subtitle restyle in `assemble.py`

**Files:**
- Modify: `cogni/assemble.py` (add `_ass_color`, `_subtitle_style`; use it in `_scene_clip`)
- Modify: `config.yaml` (`video.subtitle` block)
- Test: `tests/test_assemble_subtitles.py`

**Interfaces:**
- Consumes: `cfg["video"]["subtitle"]` (optional dict; all keys default).
- Produces: `_ass_color(hex_rgb: str, alpha: int = 0) -> str` (returns `&HAABBGGRR`); `_subtitle_style(cfg: dict) -> str` (libass `force_style` string).

- [ ] **Step 1: Write failing tests for the subtitle helpers**

Create `tests/test_assemble_subtitles.py`:

```python
from cogni import assemble

def test_ass_color_cream_opaque():
    # #F1EDE4 -> BGR E4EDF1, alpha 00
    assert assemble._ass_color("F1EDE4", 0) == "&H00E4EDF1"

def test_ass_color_teal_semi():
    # #14332E -> BGR 2E3314, alpha 0x78
    assert assemble._ass_color("14332E", 0x78) == "&H782E3314"

def test_subtitle_style_uses_config_and_palette():
    cfg = {"video": {"subtitle": {"font": "Trebuchet MS", "font_size": 16,
                                   "text_color": "F1EDE4", "box_color": "14332E",
                                   "box_alpha": 120, "margin_v": 60}}}
    s = assemble._subtitle_style(cfg)
    assert "FontName=Trebuchet MS" in s
    assert "PrimaryColour=&H00E4EDF1" in s
    assert "BackColour=&H782E3314" in s
    assert "MarginV=60" in s

def test_subtitle_style_defaults_when_absent():
    s = assemble._subtitle_style({"video": {}})
    assert "FontName=" in s and "PrimaryColour=" in s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_assemble_subtitles.py -v`
Expected: FAIL (`AttributeError: _ass_color` / `_subtitle_style`).

- [ ] **Step 3: Add the helpers to `assemble.py`**

Add near the top of `cogni/assemble.py` (after `_MUSIC_EXTS`):

```python
def _ass_color(hex_rgb: str, alpha: int = 0) -> str:
    """#RRGGBB -> libass &HAABBGGRR (AA: 00=opaque, FF=transparent)."""
    h = hex_rgb.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def _subtitle_style(cfg: dict[str, Any]) -> str:
    """libass force_style for burned subtitles, from config (Riso palette defaults)."""
    sub = cfg.get("video", {}).get("subtitle", {}) or {}
    font = sub.get("font", "Trebuchet MS")
    size = int(sub.get("font_size", 16))
    text = _ass_color(str(sub.get("text_color", "F1EDE4")), 0)          # cream, opaque
    box = _ass_color(str(sub.get("box_color", "14332E")),
                     int(sub.get("box_alpha", 120)))                    # dark teal, soft
    border_style = int(sub.get("border_style", 3))                     # 3 = opaque box
    outline = int(sub.get("outline", 0))
    shadow = int(sub.get("shadow", 0))
    margin_v = int(sub.get("margin_v", 60))
    return (f"FontName={font},FontSize={size},PrimaryColour={text},"
            f"BackColour={box},BorderStyle={border_style},Outline={outline},"
            f"Shadow={shadow},Alignment=2,MarginV={margin_v}")
```

- [ ] **Step 4: Use the helper in `_scene_clip`**

In `cogni/assemble.py`, inside `_scene_clip`, replace the inline `style = (...)` block (the multi-line `"FontName=DejaVu Sans,..."` assignment) with:

```python
        style = _subtitle_style(cfg)
```

Leave the `subs_arg = str(subs).replace("\\", "/").replace(":", r"\:")` line and the `vchain += f",subtitles='{subs_arg}':force_style='{style}'"` line unchanged.

- [ ] **Step 5: Add the `video.subtitle` block to `config.yaml`**

In `config.yaml`, under `video:` (after the `subtitles: true` line), add:

```yaml
  # Burned-subtitle look (Risograph theme). Colors are #RRGGBB.
  subtitle:
    font: "Trebuchet MS"     # any installed font; a cleaner face than the old DejaVu
    font_size: 16
    text_color: "F1EDE4"     # cream
    box_color: "14332E"      # dark teal backing
    box_alpha: 120           # 0=solid .. 255=invisible (soft bar)
    border_style: 3          # 3 = opaque box behind text
    outline: 0
    shadow: 0
    margin_v: 60             # lift off the bottom edge
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_assemble_subtitles.py -v`
Expected: all 4 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add cogni/assemble.py config.yaml tests/test_assemble_subtitles.py
git commit -m "feat(assemble): config-driven Riso subtitle style (cream on soft teal)"
```

---

### Task 4: Set Brian voice + Phase-1 dry run (hear/see the new direction)

**Files:**
- Modify: `config.yaml` (`tts.voice`)

**Interfaces:** consumes the rewritten `script`, `narrate`, and `assemble` from Tasks 2–3. Produces reviewable artifacts for the user: new `scenes.json`, new narration mp3s, one subtitle-preview PNG.

- [ ] **Step 1: Set the Cognibot voice**

In `config.yaml`, change the `tts.voice` line to:

```yaml
  voice: "en-US-BrianMultilingualNeural"
```

- [ ] **Step 2: Back up the current Rich Dad scenes (non-destructive)**

Run:
```bash
cp projects/rich-dad-poor-dad/scenes.json projects/rich-dad-poor-dad/scenes.pre-cognibot.json
```
Expected: backup file exists (the old narration/animate setup is preserved; `output/test_high.mp4` already preserves the "before" video).

- [ ] **Step 3: Regenerate the Rich Dad short script (Cognibot + character)**

Run: `.venv\Scripts\python.exe main.py script --force`
Expected: `[script] short mode — Cognibot writing the character's story ...` then `N scenes drafted around <Name>.` `scenes.json` now has a top-level `"character"` and story narration.

- [ ] **Step 4: Observation — read the new narration**

Open `projects/rich-dad-poor-dad/scenes.json`. Confirm: a named protagonist; scene 1 is a relatable cold-open problem (no verdict); later scenes teach an idea via the character AND include Cognibot's honest take; the close has an overall verdict. If it reads as a flat summary or drops the verdict, adjust the `_build_prompt` wording and re-run (this is the creative gate).

- [ ] **Step 5: Narrate in Brian's voice**

Run: `.venv\Scripts\python.exe main.py narrate --force`
Expected: `provider=edge voice=en-US-BrianMultilingualNeural — N narrated`. Listen to `projects/rich-dad-poor-dad/audio/scene_001.mp3` — natural, clear, Brian.

- [ ] **Step 6: Render one subtitle-preview frame with the new style**

Reuse an existing still + its new SRT to preview the restyle without a full render. Run:
```bash
P=projects/rich-dad-poor-dad
IMG=$(ls $P/images/scene_001.png)
.venv/Scripts/python.exe -c "
from cogni.config import load_config
from cogni.assemble import _subtitle_style
import subprocess, pathlib
cfg = load_config()
srt = pathlib.Path('$P/audio/scene_001.srt')
sub = str(srt).replace('\\\\','/').replace(':', r'\:')
style = _subtitle_style(cfg)
out = pathlib.Path('$P/output/subtitle_preview.png')
vf = f\"scale=1920:1080,subtitles='{sub}':force_style='{style}'\"
subprocess.run(['ffmpeg','-y','-v','error','-i','$IMG','-vf',vf,'-frames:v','1',str(out)], check=True)
print('wrote', out)
"
```
Expected: `projects/rich-dad-poor-dad/output/subtitle_preview.png` exists. (If scene_001 has no image yet from the new run, use any existing PNG under `$P/images/`.)

- [ ] **Step 7: Observation — user reviews the three artifacts**

Show the user: (a) the new `scenes.json` narration, (b) `audio/scene_001.mp3`, (c) `output/subtitle_preview.png`. This is the Phase-1 gate: does the narration teach-via-story with verdicts, does Brian fit, does the subtitle look Riso? Note tweaks for a follow-up before Phase 2.

- [ ] **Step 8: Commit the config**

```bash
git add config.yaml
git commit -m "feat(config): Cognibot voice (Brian) for narration"
```

(Generated project artifacts under `projects/rich-dad-poor-dad/` are not committed here — they're regenerable outputs for review.)

---

## Self-Review

**Spec coverage (Phase 1 items):**
- Delete 6 stale skills → Task 1. ✅
- Rewrite `script.py` to Cognibot character-story (short mode, verdict woven) → Task 2. ✅
- `tts.voice` = Brian → Task 4 Step 1. ✅
- Subtitle Riso restyle in `assemble.py` → Task 3. ✅
- Regenerate short script + narrate + subtitle preview for review → Task 4. ✅
- Character consistency field (`character`) → Task 2 (stored on doc; consumed by visuals in Phase 2). ✅

**Placeholder scan:** No TBD/TODO; every code step shows full code; observation steps (Task 4 Steps 4/7) are explicit manual gates, not vague "handle edge cases." ✅

**Type consistency:** `_validate_character` returns `dict|None` and is stored as doc `character`; `_generate_short` returns `(list, {"character": ...})` matching the existing `**extra` spread in `script()`; `_subtitle_style(cfg)` / `_ass_color(hex, alpha)` names match between `assemble.py` and the tests. ✅

**Out-of-scope, intentionally deferred:** long-mode Cognibot rewrite, beat granularity (Phase 2), LOW/MEDIUM/HIGH modes + mode-aware assemble + dissolves + `cogni-animate`/`motion.md` updates (Phase 3).
