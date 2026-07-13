---
name: cogni-animate
description: Turn Project Cogni's animate-flagged scenes into Higgsfield start->end hero clips and re-assemble the video. Use when the user wants to animate scenes, add motion / hero clips, or run the Higgsfield step for the active book. Requires the Higgsfield MCP connected (see the `higgsfield` skill).
---

# Cogni — animate scenes with Higgsfield (start → end)

Each scene flagged **animate=true** becomes a moving hero clip built from its **two
keyframes** — `scene_XXX.png` (start) and `scene_XXX_end.png` (end) — interpolated
by Higgsfield **Seedance 2.0** with the scene's `video_prompt` as the motion. The
clip drops into `projects/<book>/clips/scene_XXX.mp4`, and `assemble` uses it (looped
to the narration length) instead of the still. Un-flagged scenes stay Ken Burns stills.

The project leans toward animating **every** scene, but cost scales with the number
of clips — so **start small when testing** (one scene), confirm it looks right, then
scale up.

## Prerequisites

- The **Higgsfield MCP** is connected and OAuth'd (see the `higgsfield` skill for the
  `claude mcp add … https://mcp.higgsfield.ai/mcp` + `/mcp` setup). It bills the user's
  **subscription credits**.
- Run **`select_workspace`** once at the start of the session (generation fails silently otherwise).
- The active book has `script` → `visuals` → `review` → `images` done, so each animate
  scene has BOTH `images/scene_XXX.png` and `images/scene_XXX_end.png`.

Use the venv Python: `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` on macOS/Linux.

## Steps

1. **See what's flagged and ready** (from the repo root):
   ```
   .venv\Scripts\python.exe main.py animate
   ```
   Lists each animate scene with its start/end keyframe status and target clip path.
   Skip scenes that already have a clip (unless redoing) or whose keyframes are missing
   (run `images` first).

2. **Preflight the exact cost, then quote it — non-negotiable.** Call `generate_video`
   with `get_cost: true` (same params as the real call below) to get the credit cost
   for ONE clip without submitting. Multiply by the number of scenes to animate, show
   `balance` before, and **wait for the user's explicit "go".** For a first test, do a
   single scene.

3. **For each flagged scene** — upload both keyframes, then interpolate:
   1. Upload the **start** still (`images/scene_XXX.png`): `media_upload` →
      `curl -X PUT` the bytes → `media_confirm` → `start_media_id`.
   2. Upload the **end** still (`images/scene_XXX_end.png`) the same way → `end_media_id`.
   3. `generate_video`:
      - `model`: `seedance_2_0`  (supports start-frame + end-frame interpolation)
      - `medias`: `[{ "value": <start_media_id>, "role": "start_image" },
                    { "value": <end_media_id>,   "role": "end_image" }]`
      - `prompt`: the scene's **`video_prompt`** — subtle, slow, cinematic motion from the
        start frame to the end frame that preserves the Risograph look; gentle parallax /
        drift, calm and contemplative, NO camera shake, NO new characters or faces.
      - `duration`: **4**  (explicit — Seedance defaults higher = more credits)
      - `params`: `resolution: "720p"`, `mode: "fast"` (the value sweet spot; assemble
        upscales), `aspect_ratio: "16:9"`, **`generate_audio: false`** (we add our own
        narration — never pay for or burn in TTS-clashing audio).
   4. Poll `job_status({ job_id, sync: true })` until done; take **`rawUrl`**.
   5. Save it into the pipeline:
      ```
      .venv\Scripts\python.exe -c "from cogni.animate import save_clip; save_clip(<scene_id>, '<rawUrl>')"
      ```
      (accepts an https URL or a local path; writes `clips/scene_XXX.mp4` and records
      `clip_path` in scenes.json.)

4. **Re-assemble** once the clip(s) are saved:
   ```
   .venv\Scripts\python.exe main.py assemble --force
   ```
   Animated scenes now play their clip (looped to the narration length); the rest stay
   Ken Burns stills.

## Guardrails

- **Start small / quote first.** Always `get_cost` and get an explicit "go" before
  spending. When testing, animate ONE scene and review it before scaling to all.
- **Silent clips.** Always `generate_audio: false` — the video carries our own TTS
  narration; native audio would clash and cost more.
- **Two keyframes, no text→video fallback.** If an image upload fails, surface the
  error — don't fall back to text→video, which loses the visual anchor.
- If a generation errors mysteriously, suspect **plan-tier gating** or a lapsed
  subscription (check `/mcp` and `balance`) before debugging the prompt.
