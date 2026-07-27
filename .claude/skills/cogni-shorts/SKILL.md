---
name: cogni-shorts
description: Use when turning a finished Cognibot book video into vertical Shorts / TikToks / Reels — clipping an arc from an existing cut, or building a purpose-made vertical short from a book's best idea.
---

# Cogni — book video → vertical Shorts

Cut 1080×1920 Shorts from assets we already own. Unlike OpusClip/Klap (which
*detect* highlights in talking-head footage), our `scenes.json` already has the
structure — per-beat mp3, still, `duration_sec`, and subtitle `.srt`. A Short is
therefore **select an arc → reframe → re-time captions**, not highlight-detection.

**PILOT-GATE:** the one thing that can't be settled on paper is whether our 16:9
low-poly stills read well cropped to vertical. Cut ONE short, judge it against the
3-second test below, THEN batch. Fold what you learn back into this skill.

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

## Reframe: crop vs pad
- **Center-crop to 9:16** when the composition is centered with negative space — most of
  our single-subject / metaphor-object beats (hourglass, chain, frog-on-plate, ref-locked
  author shots). Looks native.
- **Blur-pad** (image floating in a blurred fill) when the composition is a left-right
  **split or wide** (pool-vs-gun, desk-split-in-two) — a crop would bisect both subjects.
- Never center-crop a split beat. When unsure, pad (safe) and note it for the pilot.

## Build mechanics
- Canvas 1080×1920, 30fps. Reuse the beat mp3s (concat in order); no re-narrate for Model A.
- Reframe with ffmpeg — crop: `crop=ih*9/16:ih,scale=1080:1920`; pad:
  `split[a][b];[a]scale=1080:1920,boxblur=40[bg];[b]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2`.
- Hook card + kinetic captions + punch-in: Remotion (reuse `Thumbnail`/`Misreg` type
  style, the `.srt` word timings drive the captions).
- The reusable encapsulation is `scripts/shortify.py <slug> <beat-start> <beat-end>` —
  build it during the pilot; until then the ffmpeg recipe above is the spec.

## Upload
Gate on the **parent video being PUBLIC** (a Short is a trailer; its "full verdict" link
must resolve). **Drip** 3–4 across the week+, don't dump. Same file → YouTube + TikTok +
Reels (the Higgsfield MCP can publish to TikTok). Link the long video in the description.

## Common mistakes
- Slow Ken Burns as the opener — too slow for a 1.5s window. Lead with the text hook.
- Clipping a mid-arc beat — no cold-open line, dies in 2s.
- One still held the whole time — reads as dead. Cut every 2–4s.
- Center-cropping a split composition — bisects both subjects. Pad instead.
- Shipping all 7 acts — weak Shorts are first impressions. Ship 3–4 strong.
