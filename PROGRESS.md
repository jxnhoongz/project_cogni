# Project Cogni — Progress

> **DEFINITION OF DONE:** Done = ONE finished video I have actually posted. Not a
> working repo. The pipeline automates ASSEMBLY only. It does NOT pick the book,
> record my voice, or fix my Khmer — those are mine.

## The Plan (one line)
Upload a book PDF → generate an English + natural spoken Khmer script → I record my
OWN Khmer voice → auto-assemble a 16:9 long-form video (still images with a subtle
Ken Burns zoom, optional Higgsfield "hero" clips, background music) → I review and
upload manually.

## Current State
Re-founded around the own-voice Khmer long-form pipeline. Old TTS / shorts / scale /
auto-distribution foundation stripped out. Rebuilding the core (see build order).

## Backbone
A single `scenes.json` that each stage enriches. Every stage is a standalone function
+ CLI subcommand, independently re-runnable, and cached (re-running reuses files unless
`--force`). All state lives on disk so any stage re-runs alone.

## Build Order
Do NOT one-shot — pause after each for me to test.

| # | Stage | Status |
|---|-------|--------|
| 0 | Phase 0 re-foundation commit | ✅ Done |
| 1 | Skeleton: config.yaml, .env.example, CLAUDE.md, `call_llm` helper | ✅ |
| 2 | `convert` — PDF/epub/docx → markitdown → `input/book.md` | ✅ |
| 3 | `ingest` — book.md → title + thesis + 6–12 key ideas → `outline.json` | ✅ |
| 4 | `script` — outline → scenes (EN first, then spoken Khmer via Gemini) + `recording_script.txt` + `check-audio` | ✅ |
| — | **[MANUAL]** I edit Khmer + record (deferred to the web UI — will record there) | ⬜ |
| 5 | `images` — scene → generate_image() → `images/scene_XXX.png` (mock done; real provider pending) | 🟡 mock |
| 6 | `assemble` — measure audio, still + Ken Burns (or clip), music, → `output/final.mp4` (1920×1080) | ✅ |
| 7 | Higgsfield drop-in — flag `animate=true`, generate clip via MCP, drop into `clips/`, re-run assemble | ⬜ |
| 8 | Gradio UI — thin wrapper over pipeline functions | ✅ |

## Stages (detail)
- **0. convert** — uploaded PDF/epub/docx → markitdown → `input/book.md`
- **1. ingest** — book.md → title + thesis + 6–12 key ideas (cheap model) → `outline.json`
- **2. script** — outline → scenes array:
  - a) `narration_en` first (strong model)
  - b) `narration_km` = NATURAL SPOKEN Khmer conveying the English meaning, NOT literal
    translation. Route Khmer to Gemini via OpenRouter. Use `khmer_style_examples.txt`
    as few-shot if present.
  - c) an `image_prompt` per scene.
  - Save `scenes.json` + `recording_script.txt`. THEN STOP.
- **3. [MANUAL]** — I edit Khmer in the UI, record each scene, upload as
  `audio/scene_001.wav …`. `check-audio` verifies every scene has a matching file.
- **4. images** — each scene → `generate_image(image_prompt)` → `images/scene_XXX.png` (cached).
- **5. assemble** — per scene: measure audio duration; if `clips/scene_XXX.mp4` exists
  use it, else still image + subtle Ken Burns; optional burned captions. Concatenate in
  id order, mix low-volume music from `assets/audio/`, export `output/final.mp4`
  (1920×1080, H.264).

## Cross-cutting
- One `call_stage(cfg, stage, prompt, ...)` helper. Each stage's provider+model is set
  in `config.yaml`: provider `claude` runs the local `claude` CLI (billed to the Claude
  subscription, NOT per-token) for Claude models; provider `openrouter` (per-token) is
  used only for models the subscription can't reach — Gemini for Khmer. Structured JSON
  + safe parsing.
- Every stage caches; re-running reuses files unless `--force`.
- `main.py` subcommands: `convert, ingest, script, check-audio, images, assemble`.
  `app.py` launches the UI.
- Fail loudly on missing files/keys.
- Visual style is NOT decided yet: a single STYLE token in `docs/STYLE.md`, appended to
  EVERY image_prompt. Placeholder `[STYLE TBD]` for now.

## Kept + adapted from the old build
- `video-renderer/` → reworked for 16:9 long-form (ffmpeg + caption logic)
- `copyright-compliance-checker/` → guardrail
- `script-quality-checker/` → esp. `references/generic_phrases.md`
- `asset-librarian/generate_image.py` → reworked into a pluggable `generate_image()` provider
- `midform-script-generator/` → folded into the EN+KM script stage
- `data/books.json` → same shape, repointed at my own sources
