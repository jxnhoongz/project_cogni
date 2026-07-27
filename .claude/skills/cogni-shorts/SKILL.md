---
name: cogni-shorts
description: Use when turning a finished Cognibot book video into vertical Shorts / TikToks / Reels — clipping an arc from an existing cut, or building a purpose-made vertical short from a book's best idea.
---

# Cogni — book video → vertical Shorts

Cut 1080×1920 Shorts from assets we already own. Unlike OpusClip/Klap (which
*detect* highlights in talking-head footage), our `scenes.json` already has the
structure — per-beat mp3, still, `duration_sec`, and subtitle `.srt`. A Short is
therefore **select an arc → reframe → re-time captions**, not highlight-detection.

**Pilot done (Atomic Habits "37× is fake math", 2026-07).** Validated: our 16:9 low-poly
stills crop to vertical and look native; the puzzle hook + brand cards carry; whole thing
$0 on reused stills. Two findings baked in below: (1) crop toward the subject, don't pad;
(2) **dual-track pacing** — v0 held one still per narration beat (~11s each) and dragged;
the fix is a visual track that cuts every ~2-4s independent of the narration boundaries.

## The two models

| Model | Cost | Use for |
|---|---|---|
| **A — clip an existing cut** | $0 | New puzzle-format books (#6+). Arcs already stand alone. |
| **B — purpose-build vertical** | ~$0.20 | Old protagonist-format books (#1–5). No clean arcs to clip; write a fresh ~120-word puzzle-first script, narrate (edge-tts, free), gen ~5 stills composed for 9:16. |

Ship **3–4 per book, not one per act.** Every Short is a first impression; a weak one
costs more than the upload gains. Quality-gate to the arcs that stand alone cold.

## What makes a beat range short-worthy
- Beat 1 has a **cold-open line** — a second-person question or flat claim that stops a
  scroll with no setup (our puzzle hooks already do this: *"There's one email in your
  inbox, still unread, six days old…"*).
- Self-contained **puzzle→payoff** OR a single striking verifiable fact (the
  Thinking-Fast-&-Slow replication beat clips perfectly; a mid-arc beat does not).
- 4–8 beats, **~35–60s** total (sum `duration_sec`).

## The retention recipe (research-grounded — the 1.3–1.8s swipe window is real)
1. **Frame 1 = a big text hook**, before the zoom or the first spoken word. People
   scroll muted; the *line they read* stops them, not the image. Same skill as our
   thumbnails. Two-beat reveal works ("Every guru quotes this study." → "It doesn't exist.").
2. **No bumper.** Never the channel intro. Cold-open on the hook.
3. **Refresh every 2–4s** — hard-cut to the next still; hold nothing for 10s.
4. **Punch-in per cut** — 0.3s scale-up when each still lands. Cheap motion = "alive."
5. **Kinetic captions** — big centered words popping one-by-one from the beat `.srt`.
   The text moving covers for the still not moving.
6. **End on the curiosity gap + CTA** — "full verdict on the channel," 1s cover card.

Target VVSA 70–90% / avg-%-viewed >80%. The 3-second test: **if it doesn't stop *you*
scrolling, it won't stop a stranger** — re-cut before shipping.

## Reframe: crop toward the subject (pilot-validated on real stills, 2026-07)
**Crop is the default and it looks native** — a 9:16 slice of a centered low-poly beat
(spotlit figure, walking figure, metaphor object) is indistinguishable from a made-for-
vertical shot. The variable is *where* the crop window sits, not whether to pad:
- **Centered subject → center-crop.** `crop=ih*9/16:ih`.
- **Off-center subject → bias the window toward it.** `crop=ih*9/16:ih:x=<offset>` — a
  blind center-crop on a left-placed figure cropped him out entirely (verified). Per-beat
  `crop_x` knob; eyeball the subject's side.
- **Blur-pad is a weak last resort, not the safe default.** Our art is wide, so padding
  leaves big blurred dead-bands and a tiny subject. Reserve it for genuine two-subjects-
  far-apart splits (pool-vs-gun) — and prefer just picking a beat that crops, or a slow pan.

## Build mechanics (BUILT — this is the pipeline)
A short is a hand-authored spec + one command:
1. **Author `shorts/<slug>.json`** (see `shorts/atomic-habits-37x.json`): `narration`
   (one line per beat, plain second-person), and `shots` — the VISUAL track, cut every
   ~2-4s. Each shot is a brand card (`kind:"hook"|"end"` + `cap`) or a book still
   (`scene:<id>`, `pos:"x% y%"` crop bias, `dur`, `cap:[line1, line2?]`). The two tracks
   run in parallel, so `sum(shot durs) ≈ sum(narration durs)`.
2. **`python scripts/shortify.py shorts/<slug>.json`** narrates each line (plain
   `en-US-BrianNeural`), measures durations, stages stills + music into `remotion/public`,
   warns if the tracks drift >0.4s, and renders the Remotion `Short` composition to
   `projects/<book>/shorts/<slug>.mp4`. `--no-render` stages only.
- The `Short` composition (`remotion/src/Short.tsx`) is generic: dual-track (continuous
  narration + independent shot cuts), CSS crop-toward-subject via `object-position`,
  per-shot push-in, big two-line captions (cream + ochre), brand hook/end cards.
- Captions are per-shot punch phrases (2-4 words), NOT the full `.srt` — shorts-native.

## Upload
Gate on the **parent video being PUBLIC** (a Short is a trailer; its "full verdict" link
must resolve). **Drip** 3–4 across the week+, don't dump. Same file → YouTube + TikTok +
Reels (the Higgsfield MCP can publish to TikTok). Link the long video in the description.

## Common mistakes
- Slow Ken Burns as the opener — too slow for a 1.5s window. Lead with the text hook.
- Clipping a mid-arc beat — no cold-open line, dies in 2s.
- One still per narration beat (~11s holds) — reads as dead. Decouple: visual cuts
  every 2–4s over continuous narration (the v0→v1 fix).
- A hook card that sits static while a long hook line plays — cut to imagery after ~3s.
- Blind center-crop on an off-center subject — crops them out. Bias `pos` toward them.
- Shipping all 7 acts — weak Shorts are first impressions. Ship 3–4 strong.
