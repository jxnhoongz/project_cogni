---
name: cogni-animate
description: Turn Project Cogni's animate-flagged scene stills into Higgsfield hero clips and re-assemble the video. Use when the user wants to animate scenes, add motion / hero clips, or run the Higgsfield step for the active book. Requires the Higgsfield MCP connected (see the `higgsfield` skill).
---

# Cogni — animate hero scenes with Higgsfield

Only scenes the user flagged **animate=true** become moving hero clips (image→video);
every other scene stays a Ken Burns still. This keeps credit cost low. The generated
clip drops into `projects/<book>/clips/scene_XXX.mp4`, and `assemble` uses it (looped
to the narration length) instead of the still.

## Prerequisites

- The **Higgsfield MCP** is connected and OAuth'd (see the `higgsfield` skill for the
  `claude mcp add … https://mcp.higgsfield.ai/mcp` + `/mcp` setup). It bills the user's
  **subscription credits**.
- Run **`select_workspace`** once at the start of the session (generation fails silently otherwise).
- The active book already has `script` + `images` done (the stills must exist).

## Steps

1. **See what's flagged** (from the repo root, using the venv python):
   ```
   .venv/bin/python main.py animate
   ```
   This lists each animate-flagged scene, its still path, and target clip path. Skip
   scenes that already have a clip (unless the user wants a redo) or have no still.

2. **ALWAYS quote credit cost first** (non-negotiable — from the `higgsfield` skill's
   cost table). Default model **`seedance_1_5`** at **720p, 4s ≈ ~2.4 credits/clip**
   (`kling_3_0` for higher quality). Multiply by the number of clips, show `balance`
   before/after, and **wait for explicit "go".**

3. **For each flagged scene** (its still is `projects/<book>/images/scene_XXX.png`):
   1. Upload the still — `media_upload` → `curl -X PUT` the bytes → `media_confirm` → `media_id`.
   2. `generate_video`:
      - `model`: `seedance_1_5` (or `kling_3_0`)
      - `medias`: `[{ "value": <media_id>, "role": "start_image" }]`  (Kling/Seedance use `start_image`)
      - **`duration`: 4** (explicit! Seedance 1.5 defaults to 12s = 3× cost)
      - resolution 720p+ (assemble upscales to 1080p; 720p is the value sweet spot)
      - prompt: **subtle, slow, cinematic motion that preserves the Risograph still** —
        gentle parallax / drift, the scene quietly coming alive, calm and contemplative,
        NO camera shake, NO new characters or faces. Derive the subject from the scene's
        `image_prompt`.
   3. Poll `job_status({ job_id, sync: true })` until done; take **`rawUrl`**.
   4. Save it into the pipeline:
      ```
      .venv/bin/python -c "from cogni.animate import save_clip; save_clip(<scene_id>, '<rawUrl>')"
      ```
      (accepts an https URL or a local path; writes `clips/scene_XXX.mp4` and records
      `clip_path` in scenes.json.)

4. **Re-assemble** once all clips are saved:
   ```
   .venv/bin/python main.py assemble --force
   ```
   The hero scenes now play their clip (looped to the narration length); the rest stay
   Ken Burns stills.

## Guardrails

- **Hero scenes only.** Don't offer to animate every scene of a long video — that's the
  expensive move. A handful of clips per video.
- **Don't fall back to text→video** if a still upload fails — that loses the visual anchor.
  Surface the error.
- If a generation errors mysteriously, suspect **plan-tier gating** or a lapsed subscription
  (check `/mcp` and `balance`) before debugging the prompt.
