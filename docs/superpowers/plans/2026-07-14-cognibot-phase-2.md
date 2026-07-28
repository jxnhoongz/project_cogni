# Cognibot Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans / subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Produce the first full watchable cut of the new direction — images that track the narration beat-by-beat (killing the car/tree mismatch) with a consistent protagonist — still-only (no Higgsfield yet).

**Architecture:** The Phase-1 script already emits one per-beat `image_prompt` per scene. `images.py` already falls back to `image_prompt` when `start_image_prompt` is empty, and `review_gate` skips scenes without `start_image_prompt` — so the new scenes need no `visuals`/`review` detour. The only code change is threading the doc-level `character` description into each image prompt for visual consistency. Then generate the stills and assemble the Ken Burns + Brian + Riso-subtitle cut.

**Tech Stack:** Python (`cogni/`), OpenRouter image gen (gemini-2.5-flash-image, ~$0.04/image), ffmpeg.

## Global Constraints

- Windows; run `.venv\Scripts\python.exe`. Preserve the `scenes.json` schema.
- Image cost for a 14-beat script ≈ **$0.56** (cheap; user has authorized the pipeline). No Higgsfield in Phase 2 (that's Phase 3).
- Art STYLE token (`docs/STYLE.md`) unchanged; silhouettes/no-faces stays.
- Branch: `claude/cognibot-redesign`.

## File Structure

- `cogni/images.py` — **modify**: add `_image_prompt(base, character, style)` helper; read `doc["character"]` and thread it.
- `tests/test_images.py` — **create**: unit tests for `_image_prompt`.

---

### Task 1: Character-consistent image prompts

**Files:**
- Modify: `cogni/images.py`
- Test: `tests/test_images.py`

**Interfaces:**
- Produces: `_image_prompt(base: str, character: dict | None, style: str) -> str` — joins the beat prompt + an optional "recurring character" clause + the STYLE token.

- [ ] **Step 1: Write failing tests**

Create `tests/test_images.py`:

```python
from cogni import images


def test_image_prompt_threads_character():
    p = images._image_prompt(
        "a kitchen at night",
        {"name": "Dana", "description": "woman in blue scrubs, hair in a bun, seen from behind"},
        "RISO STYLE",
    )
    assert "a kitchen at night" in p
    assert "blue scrubs" in p
    assert "RISO STYLE" in p


def test_image_prompt_no_character():
    assert images._image_prompt("a desk", None, "STYLE") == "a desk STYLE"


def test_image_prompt_empty_character_desc():
    assert images._image_prompt("a desk", {"name": "X", "description": ""}, "STYLE") == "a desk STYLE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_images.py -v`
Expected: FAIL (`AttributeError: _image_prompt`).

- [ ] **Step 3: Add the helper**

In `cogni/images.py`, add above `def images(`:

```python
def _image_prompt(base: str, character: dict[str, Any] | None, style: str) -> str:
    """Beat prompt + optional recurring-character clause + STYLE token."""
    parts = [base.strip()]
    desc = ((character or {}).get("description") or "").strip()
    if desc:
        parts.append(f"Recurring character, only if a person appears in this shot: {desc}.")
    if style.strip():
        parts.append(style.strip())
    return " ".join(p for p in parts if p).strip()
```

- [ ] **Step 4: Thread the character in `images()`**

In `cogni/images.py`, inside `images()`, after `scenes = doc.get("scenes", [])` (and its emptiness check), add:

```python
    character = doc.get("character")
```

Then replace the start-keyframe generation line:

```python
            generate_image(f"{base} {style}".strip(), start_out, cfg, label=f"Scene {s['id']}")
```

with:

```python
            generate_image(_image_prompt(base, character, style), start_out, cfg, label=f"Scene {s['id']}")
```

(Leave the end-keyframe branch as-is — no animate scenes in Phase 2.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_images.py -v`
Expected: 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add cogni/images.py tests/test_images.py
git commit -m "feat(images): thread recurring-character description into prompts for consistency"
```

---

### Task 2: Generate stills + assemble the full cut (run + review — done inline, not a subagent)

**Files:** none (pipeline run + visual review).

- [ ] **Step 1: Generate the beat stills**

Run: `.venv\Scripts\python.exe main.py images --force`
Expected: `[images] provider=openrouter — 14 generated, 0 cached (14 scenes)`. (~$0.56.)

- [ ] **Step 2: Observation — spot-check 3–4 stills**

View e.g. `images/scene_001.png` (Dana in a dim kitchen lit by a phone), `scene_003.png` (hands, coins in/out), `scene_004.png`. Confirm: each matches its beat's narration, Dana reads as a consistent silhouette, on-style. If a beat is clearly off, note it (image-prompt tweak) — but small character drift is expected and fine for this cut.

- [ ] **Step 3: Assemble the full still cut**

Run: `.venv\Scripts\python.exe main.py assemble --force`
Expected: `output/final.mp4` — 14 beats, Ken Burns stills + Brian narration + Riso subtitles.

- [ ] **Step 4: Observation — watch for sync**

Confirm each image is on screen while its narration is spoken (no car/tree mismatch). This is the Phase 2 gate.

- [ ] **Step 5: Deliver to user** — present `output/final.mp4` + a few stills for review before Phase 3 (modes).

## Self-Review

- Sync fix (beat images track narration) → Task 1 (character) + Task 2 (generate from per-beat prompts). ✅
- Character consistency → Task 1. ✅
- Full watchable cut → Task 2 Step 3. ✅
- No placeholders; `_image_prompt` name consistent between helper, tests, and call site. ✅
- Deferred: LOW/MEDIUM/HIGH modes, dissolves, Higgsfield, `cogni-animate`/`motion.md` updates → Phase 3.
