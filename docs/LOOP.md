# The Loop — book → posted Cognibot video

The repeatable producer runbook. You drop a book file in; an agent runs these stages,
pausing once for a credit go-ahead. Everything is file-based, so any stage re-runs alone.

**Golden rule:** run every `main.py` stage with the venv, not system python —
`./.venv/Scripts/python.exe main.py <stage>`. (System python lacks `httpx`/`dotenv`,
and `main.py` imports `cogni.animate`→`httpx` at load. The venv has them.)

## Stages (happy path)

| # | Command | Credits | Notes |
|---|---------|---------|-------|
| 1 | `convert <book.pdf/epub/docx>` | free | → `projects/<slug>/book.md`, creates + activates the project |
| 2 | `ingest` | free | → `outline.json` (title, thesis, key ideas) — Claude CLI (subscription) |
| 3 | `script` | free | → `scenes.json` — invents ONE protagonist, long-mode chapters, verdict woven in |
| 4 | `script-review` → `revise` → `fact-check` | free | critique + fix weak/ungrounded scenes (optional but cheap) |
| 4b | `python scripts/check_tics.py` | free | **cross-book tic check.** Flags phrasing reused from earlier books, with scene ids. Rewrite those beats in scenes.json and re-run until it PASSES — *before* narrate, or the tic is baked into audio. Books 1-3 shipped sharing "as an instruction manual", "give the book real credit", "here's my honest take" |
| 4c | `python scripts/check_crutches.py` | free | **within-script crutch check.** Flags "honest" overuse and skeleton phrases ("here's my honest take", "X years later", "who this is for", "in this video"), with scene ids. Rewrite those beats and re-run until it PASSES — same pre-narrate slot as `check_tics.py` |
| 5 | `visuals` | free | per-scene keyframe + start/end/video prompts |
| 6 | `modes` | free | tag each beat LOW/MEDIUM/HIGH + motion prompt. Cap `max_animated` (config, now **4**). Beat 1 forced HIGH |
| 7 | `review` | free | validate visual prompts, gate generation |
| 8 | `narrate` | free | → `audio/scene_XXX.mp3` (+ `.srt`) via edge-tts (Brian voice) |
| — | **CREDIT GATE** | — | `get_cost` preflight, quote the total, WAIT for explicit "go" (cogni-animate skill) |
| 9 | `images` | see below | Three ways to buy the ~95 stills — pick per budget. STYLE.md is appended to every prompt automatically |
| 10| `animate` (list) → generate | ~36 cr/clip | Higgsfield seedance_2_0 (standard, NOT fast). Only the ~4 tagged beats. **Dispatch subagents**, 3–4 in parallel per batch (firing all at once → 429). **Pass BOTH keyframes** — `medias` role `start_image` = scene_XXX.png, role `end_image` = scene_XXX_end.png (seedance_2_0 supports first-last-frame). Anchoring to both frames stops the clip drifting into a different scene (the recurring review flag) and lands it on a controlled last frame. Books 1–4 mistakenly used start-only and never fed the end frame |
| 11| `assemble --force` | free (nvenc) | → `output/final.mp4` (stills + Ken Burns + clips + narration + subtitles + music). Writes `duration_sec` back |
| 12| **Remotion per-book** (see below) | free | chapter cards + intro/outro book title + optional count-up, rendered with ALPHA |
| 13| `scripts/finalize.py` | free (nvenc) | juice overlays + intro/outro in ONE pass → `output/final_full.mp4` ← **the upload file** |
| 14| thumbnail + `publish.md` | free | Remotion `Thumbnail` still + SEO/description/timestamps |

## Step 9 — the three ways to get the stills

| Route | Cost per book (~95 imgs) | Effort |
|---|---|---|
| **OpenRouter** (`config.yaml image.provider: openrouter`, `google/gemini-2.5-flash-image`) — just run `main.py images` | **~$4**, 0 credits | none |
| **Higgsfield API** — set provider/model to `nano_banana` (1 cr) or `nano_banana_pro` (2 cr) | **~95–190 credits**, $0 | none |
| **Manual, web app** — free but hand-clicked (below) | **$0 and 0 credits** | ~2–3 hrs |

**Manual route** (when credits/cash are tight and time isn't):
```
python scripts/export_prompts.py          # -> projects/<slug>/manual/prompts.txt + manifest.json
#   higgsfield.ai/ai/image -> Unlimited toggle ON, aspect 16:9, generate each in order,
#   save as 1.png .. N.png in one folder. KEEP THE NUMBERING.
python scripts/import_images.py <folder> --dry-run   # verifies numbering, touches nothing
python scripts/import_images.py <folder>             # renames onto scenes + stamps scenes.json
```
`import_images.py` refuses on any missing/duplicate number and warns on non-16:9 — that
numbering contract is the whole safety net (one re-roll renumbered = every later image on
the wrong scene). The web "Unlimited" toggle is free but **web-only**: the API rejects
`use_unlim` and bills credits anyway (verified), which is exactly why this manual path exists.

## Step 12 — Remotion (the per-book manual bits)

The templates are built; only the text changes per book. In `remotion/src/`:
- `Root.tsx` — set the `CHAPTERS` array to the new book's chapter titles (drives Ch1…ChN cards).
- `Intro.tsx` / `Outro.tsx` — swap the book title ("RICH DAD POOR DAD").
- (optional) a `Countup` beat if the book has a punchy number; set its scene + value.

Then render with ALPHA and copy into the project:
```
cd remotion
# transparent ProRes REQUIRES all four flags or it silently drops alpha (composites black):
npx remotion render Ch2 out/Ch2.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png
# …Ch3…ChN, Countup; intro/outro as mp4 (no alpha needed)
npx remotion render Intro out/intro.mp4 ; npx remotion render Outro out/outro.mp4
cp out/Ch*.mov out/Countup*.mov ../projects/<slug>/juice/
```
`finalize.py` auto-places a chapter card at the first scene of each chapter (Ch1 skipped so it
doesn't cover the hook). Edit its `JUICE_MAP_BASE` / `PROJ` for the new project + any count-up.

## The credit gate (never skip)

Before step 9, `get_cost` for the image + clip batch, quote it to the human, and wait for
explicit "go". ~91 images + 4 clips ≈ a few hundred credits. Check `balance` first.

## Known refinements to fold in (from book #1)

- **Freeze tail:** an 8s clip under a 15s beat freezes on its last frame. Fix: animate only
  SHORT beats (narration ≤ ~8s), and/or make `assemble` end a clip with a slow zoom on the
  last frame instead of a hard `tpad` clone.
- **Text garble:** the image/animation model invents garbled words on chart/phone/document
  beats despite STYLE.md's NO-text rule. If a beat needs data, frame it as physical objects
  (coin stacks, not a chart). If a clip garbles, drop it to its (clean) still.
- **Motion is optional:** low-poly + Ken Burns already reads as alive. Keep animation to the
  hook + a couple of punches; it's the biggest credit cost for the least visible gain.
- **Don't enumerate verdict moves in a prompt.** Books 1-3 reused the same climax scaffolding
  because `config.yaml script.angle` (injected into EVERY chapter call as "follow this
  closely") listed three fixed moves — "what it gets right / where it's overstated / who it
  helps" — and `script.py` repeated them. The model wasn't being lazy; we ordered those moves
  twice. Fixed by making the verdict derive from the book's own specifics. **Never re-add a
  fixed list of verdict beats to the angle or the chapter roles** — and note that a stronger
  model does NOT fix this: it fills the same template more elegantly.
- **Story Architect designs the verdict now.** Long-mode `script` runs a Story Architect pass
  before the chapters, emitting `doc["story"]` — the Story Bible (protagonist + wound, one
  earned book-specific argument, a central wager the book can lose, plant→payoff, closing
  scene). The verdict is designed there, not in config `script.angle`.
- **Fresh protagonist per book:** the writer defaults to "Marcus" (books 1 and 3 both got one).
  Rename to a distinct name + a visually distinct look. Marcus Webb (stocky/polo/lanyard),
  Danny Rivera (wiry/hoodie), Ray Delgado (glasses/polo/smirk).

## Estimated wall-clock (repeat book, pipeline already built)

~2–3 hours, mostly hands-off. Long pole = Higgsfield generation (images + clips) in the
background (~60–90 min). Script/narrate = minutes; assemble+finalize = ~15 min; Remotion
per-book text + render = ~15 min; my review between stages = the rest.
