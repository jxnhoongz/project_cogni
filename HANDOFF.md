# Project Cogni — Handoff / Machine Setup

Pick this up on a new machine (or a fresh Claude Code session). The chat and the
generated assets don't travel with `git`; this doc + the code do.

## What this is
Book → honest **verdict** script (a point of view, NOT a summary) → **TTS**
narration → auto-assembled 16:9 video (Risograph stills with Ken Burns, optional
Higgsfield hero clips, synced subtitles, background music). English, general
audience. Definition of done = one posted video.

## Where things stand (2026-07-13)
- Pivoted **away from own-voice Khmer** (my Khmer isn't strong enough) to **TTS +
  English verdict**. Narrator voice: edge-tts `en-GB-RyanNeural`.
- Full pipeline works end to end. First video made: **Rich Dad Poor Dad**
  (11 scenes, ~4.3 min), with 2 Higgsfield hero clips (scenes 1 & 11) and synced
  subtitles.
- Rendering uses the **Apple VideoToolbox** hardware encoder (quiet/fast on Apple
  Silicon); `config.yaml video.encoder: x264` for software.
- Latest work is on branch `claude/tts-pipeline`/`claude/tts-pivot` (PR #13) — make
  sure it's merged into `main` before cloning elsewhere.

## Pipeline (each a `main.py` subcommand; caches; `--force` to redo)
`convert → ingest → script → narrate → images → assemble`
(+ `check-audio`, `animate` for Higgsfield hero clips, `projects` to list books.)
Each book is a project under `projects/<slug>/` (gitignored — book text may be
copyrighted). One active book at a time (`.active_project`).

## Key decisions
- **LLM routing** (`config.yaml llm`): provider `claude` = local `claude` CLI
  (Claude **subscription**, not per-token) for ingest + script. `openrouter`
  (per-token) is used ONLY for image generation.
- **Images:** OpenRouter `google/gemini-2.5-flash-image`, 16:9, ~$0.04/image.
- **TTS:** edge-tts (free), Ryan voice; emits a synced `.srt` per scene → burned
  as subtitles by `assemble`.
- **Higgsfield hero clips:** via the **hosted MCP** (`mcp.higgsfield.ai`, OAuth =
  **subscription** credits, no API key). Flow: flag `animate=true` scenes → the
  `cogni-animate` skill drives image→video (Kling 3.0 Turbo, start_image) → clips
  land in `clips/scene_XXX.mp4` → re-assemble. Cost-gated.

## New-machine setup
1. `git clone` the repo (after PR #13 is merged), `cd` in.
2. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. System deps: `brew install ffmpeg tesseract`
4. `cp .env.example .env` and set `OPENROUTER_API_KEY` (image gen).
5. `claude` logged into the Claude subscription (for ingest/script).
6. Higgsfield MCP: `claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp` then `/mcp` (OAuth). Re-install the generic
   Higgsfield skill from `github.com/robonuggets/higgsfield-skill` into
   `~/.claude/skills/higgsfield` if you want its model/cost reference.
7. The `projects/` data (book text, images, clips, videos) is NOT in git — copy the
   folder over manually if you want to keep RDPD, or just regenerate (cheap).
8. Run the UI: `.venv/bin/python app.py` → http://127.0.0.1:7860

## Pending / next (agreed but not built)
**Schema rework for real start→end animation + a validation safety net:**
- Per-scene JSON gains `start_image_prompt`, `end_image_prompt`, `video_prompt`
  (motion start→end) — two keyframes + a motion prompt instead of one still.
- New **`visuals`** stage (creative): writes those three prompts per scene from the
  narration + STYLE.
- New **`review`** stage (validator): checks each scene's prompts are relevant to
  its narration and coherent as a start→end pair, writes `review.issues`, and
  **gates generation** (text-only, zero credits) — the safety net before spending.
- Open decision: animate **all** scenes (start+end each) vs **hero-flagged only**
  (recommended: all get a start image + prompts; `animate` decides end frame + clip).
- Build order: text-side first (schema + visuals + review, no credits), verify the
  validator on RDPD, then wire images (start/end) + animate (start→end video).

## Also open (free, high-impact)
- More/varied Ken Burns + crossfade transitions.
- Long-form script mode (chaptered, many scenes) for true 30–60 min videos.
