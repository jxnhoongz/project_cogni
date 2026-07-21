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
| 4 | `script-review` → `revise` | free | critique + fix weak scenes (optional but cheap) |
| 4a | `fact-check` | free | **RUN IT.** `script` writes from `outline.json` (~6k) plus the model's own memory — it never sees `book.md` (~300k), so invented detail is the standing risk on a channel whose premise is "I read the whole thing". A pilot script claimed Frankl's manuscript was "sewn into the lining" of his coat; the book says the inner pocket. Books 1-5 all shipped without this stage ever being run. **Read the flags, don't obey them** — the model is non-deterministic (same script, same excerpt: 3 flags then 0), and on book #5 all 3 flags were FALSE, on a quote that is verbatim in the book. False "not-in-book" flags are auto-cleared against the full text; nothing can recover a fabrication it failed to notice |
| 4b | `python scripts/check_tics.py` | free | **cross-book tic check.** Flags phrasing reused from earlier books, with scene ids. Rewrite those beats in scenes.json and re-run until it PASSES — *before* narrate, or the tic is baked into audio. Books 1-3 shipped sharing "as an instruction manual", "give the book real credit", "here's my honest take" |
| 4c | `python scripts/check_crutches.py` | free | **within-script crutch check.** Flags "honest" overuse and skeleton phrases ("here's my honest take", "X years later", "who this is for", "in this video"), with scene ids. Rewrite those beats and re-run until it PASSES — same pre-narrate slot as `check_tics.py` |
| 5 | `visuals` | free | per-scene keyframe + start/end/video prompts |
| 6 | `modes` | free | tag each beat LOW/MEDIUM/HIGH + motion prompt. Cap `max_animated` (config, now **4**). Beat 1 forced HIGH |
| 7 | `review` | free | validate visual prompts, gate generation |
| 8 | `narrate` | free | → `audio/scene_XXX.mp3` (+ `.srt`) via edge-tts (Brian voice) |
| — | **CREDIT GATE** | — | `get_cost` preflight, quote the total, WAIT for explicit "go" (cogni-animate skill) |
| 9 | `images` | see below | Three ways to buy the ~95 stills — pick per budget. STYLE.md is appended to every prompt automatically |
| 10| `animate` (list) → generate | 3.5 cr/sec | Higgsfield seedance_2_0, **720p + `mode: fast`** (52.5 cr for 15s). Only the ~4 tagged beats. **SINGLE start still** — `medias` role `start_image` = scene_XXX.png, plus the scene's `video_prompt` as a real camera move. Do NOT pass an end frame: near-identical start/end keyframes gave Seedance nothing to interpolate and **froze the clips** (`docs/motion.md`), which is why end stills were retired from `images`. Size each clip to its beat's `duration_sec` (min 5s, max 15s) so you don't buy footage that gets cut |
| 11| `assemble --force` | free (nvenc) | → `output/final.mp4` (stills + Ken Burns + clips + narration + subtitles + music). Writes `duration_sec` back |
| 12| **Remotion per-book** (see below) | free | chapter cards + intro/outro book title + optional count-up, rendered with ALPHA |
| 13| `scripts/finalize.py` | free (nvenc) | juice overlays + intro/outro in ONE pass → `output/final_full.mp4` ← **the upload file** |
| 14| thumbnail + `publish.md` | free | Remotion `Thumbnail` still + SEO/description/timestamps |
| 15| **watch the cut** | free | See below — do NOT skip, and do NOT sample only the parts you changed |

## Step 9 — the three ways to get the stills

| Route | Cost per book (~95 imgs) | Effort |
|---|---|---|
| **OpenRouter** (`config.yaml image.provider: openrouter`, `google/gemini-3.1-flash-lite-image`, "Nano Banana 2 Lite") — just run `main.py images` | **~$3.3**, 0 credits | none |
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

The templates are built; only the text changes per book. In `remotion/src/Root.tsx`:
- **`BOOK_TITLE`** — the intro's title card. It sits directly above `CHAPTERS` because it
  used to be hardcoded inside `Intro.tsx`, and book #5 shipped a cut that opened with book
  #4's title card. **Changing it means nothing until you re-render `out/intro.mp4`** —
  `finalize.py` concatenates that file as-is and will happily prepend a stale one.
- `CHAPTERS` — the new book's chapter titles (drives Ch1…ChN cards). Count must match the
  book's acts; a 6-act book leaves a stale Ch7 unused.
- (optional) a `Countup` beat if the book has a punchy number; set its scene + value, and
  pick `ink` to contrast with THAT beat's background (default TEAL vanishes on a dark one).

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

## Step 15 — watch the cut before you call it done

Sample the WHOLE runtime, not the bits you just edited. Book #5 was verified by checking
chapter cards, the count-up and all four hero clips — every element that had been touched —
and shipped with the previous book's intro, because the first five seconds were the one
place assumed safe. **Anything reused from the last book is exactly what goes stale.**

```bash
F=projects/<slug>/output/final_full.mp4
i=0; for T in 3.5 60 172 300 392 500 595 700 806 950 1021 1097 1200 1286; do
  i=$((i+1)); ffmpeg -v error -y -ss $T -i "$F" -vframes 1 -vf scale=480:-1 \
    "$SP/sheet_$(printf %02d $i).png"; done
ffmpeg -v error -y -i "$SP/sheet_%02d.png" -filter_complex tile=3x5 -frames:v 1 "$SP/sheet.png"
```

Check: **the intro title card names THIS book**, chapter cards match `CHAPTERS`, the count-up
is legible against its beat, the outro is present, the protagonist looks like one person.

Seek gotcha: `-ss` BEFORE `-i` is fast but snaps to a keyframe — fine for "which book is
this", useless for "is the overlay at the right timestamp". Put `-ss` AFTER `-i` for that
(slow: it decodes from the start).

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
