# Project Cogni

> **DEFINITION OF DONE:** Done = ONE finished video I have actually posted. Not a
> working repo. The pipeline automates ASSEMBLY only. It does NOT pick the book,
> record my voice, or fix my Khmer — those are mine.

## What this is

Upload a book PDF → generate an English + natural spoken Khmer script → I record
my OWN Khmer voice → auto-assemble a 16:9 long-form video (still images with a
subtle Ken Burns zoom, optional Higgsfield "hero" clips, background music) → I
review and upload manually.

**No TTS. My voice.** English is a reference; the Khmer is what I actually read.

## Architecture

Simple, debuggable, file-based core. Each stage is a plain function with one job,
writing all state to disk so any stage re-runs alone. No agent frameworks. The
Gradio UI is a thin wrapper that only calls pipeline functions.

**Projects (one per book).** Each book is a project folder under
`projects/<slug>/` holding `book.md`, `outline.json`, `scenes.json`,
`recording_script.txt`, and `images/ audio/ clips/ output/`. One project is
active at a time (pointer: `.active_project`); every stage reads/writes inside
it. `convert` creates + activates a project from the book filename. Background
music is shared at the repo level (`assets/audio/`). CLI: `--project <slug>` +
`projects`; UI: the Book dropdown. `config.yaml paths` are per-project; `shared`
is repo-level.

- `main.py` — CLI, one subcommand per stage.
- `app.py` — Gradio UI.
- `cogni/config.py` — config, projects/active-book, path resolution; fails loudly.
- `cogni/llm.py` — `call_stage(cfg, stage, prompt, json_out=True)`. Provider per
  stage in `config.yaml`: `claude` = local `claude` CLI (Claude subscription, not
  per-token) runs ingest + the whole script (English AND Khmer). `openrouter`
  (per-token) is used ONLY for image generation.
- `docs/STYLE.md` — single STYLE token appended to EVERY image prompt.

### The backbone: `scenes.json`

One file each stage enriches. Per scene: `id`, `narration_en`, `narration_km`
(editable), `on_screen_text`, `image_prompt`, `animate`, `audio_path`,
`image_path`, `clip_path`, `duration_sec` (measured at assemble).

### Stages (build order — see PROGRESS.md)

`convert` → `ingest` → `script` → **[I record]** → `check-audio` → `images` →
`assemble` → (Higgsfield drop-in) → Gradio UI.

Every stage caches; re-running reuses files unless `--force`. Fail loudly on
missing files/keys.

## Conventions

- LLM routing (provider + model per stage) lives in `config.yaml`, never hardcoded.
  Claude models via the subscription; OpenRouter only for what it can't reach.
- Immutable data; small focused files; validate at boundaries; no silent errors.
- Khmer is NATURAL SPOKEN meaning, NOT literal translation.
- Higgsfield clips are produced OUTSIDE this repo via its MCP and dropped into
  `clips/` — not a pipeline dependency.
