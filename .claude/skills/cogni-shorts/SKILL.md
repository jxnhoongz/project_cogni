---
name: cogni-shorts
description: Use when turning a finished Cognibot book video into vertical Shorts / TikToks / Reels — clipping an arc from an existing cut, or building a purpose-made vertical short from a book's best idea.
---

# Cogni — book video → vertical Shorts

Cut 1080×1920 Shorts from assets we already own. Unlike OpusClip/Klap (which
*detect* highlights in talking-head footage), our `scenes.json` already has the
structure — per-beat mp3, still, `duration_sec`, and subtitle `.srt`. A Short is
therefore **select an arc → reframe → re-time captions**, not highlight-detection.

**What works (validated to "uploadable", 2026-07).** The first attempts FAILED and taught
the recipe: a slideshow (one still per ~11s beat) dragged; a caption-card version hid the
text behind app UI and only soft-faded; and a *debunk* angle ("your favorite number is
fake") read as smug — the same gotcha the long-form has to avoid. What cleared the bar:
- **Teach, don't dunk.** Lead with the book's genuinely useful idea, handed over
  generously — not "this famous thing is wrong." A short has no room for the balancing
  "but here's what's good," so a pure debunk is all sneer. (See [[cognibot-tone-not-smug]].)
- **Karaoke captions** — real per-word timing (faster-whisper on our own narration), the
  line sits still and the highlight glides word-to-word; the line's **keyword holds in
  ochre**, the spoken word scales. This is "the pop subtitle thing" done right.
- **Dead-centre captions** — the bottom ~30% is buried under Shorts UI (handle, buttons,
  description). Text must live in the middle safe zone.
- **Persistent top-left book badge** (cover + title) — the one corner app UI leaves alone;
  gives instant context to a mid-scroll landing.
- Crop toward the subject (below); reused stills, $0.

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
1. **Open on the useful hook in the first ~2s**, teaching not dunking. People scroll
   muted; the karaoke caption they *read* stops them. ("Your habits don't stick — and it's
   not because you're lazy.")
2. **No channel bumper.** The persistent top-left badge carries branding instead.
3. **A still per ~4–6s segment is fine** — the karaoke captions (a new phrase every
   ~1s) + a slow push-in carry the pace; the image doesn't have to cut fast.
4. **Karaoke captions, dead-centre**, keyword in ochre, spoken word scales (in sync).
5. **~25–35s.** Hit the idea fast; don't overstay.
6. **End card** — COGNIBOT + "full verdict on the channel" + Subscribe.

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
1. **Author `shorts/<slug>.json`** (see `shorts/atomic-habits-2min.json`):
   `{ slug, book: "<proj under projects/>", title: "ATOMIC HABITS",
      cover: {title, author}, music: "<file in assets/audio>",
      segments: [ {text: "<narration line>", scene: <still id>, pos?: "x% y%"}, ... ] }`
   One segment per narration line + still; the LAST segment with `scene: null` is the
   COGNIBOT + Subscribe end card. Content = TEACH one useful idea, ~25–35s.
2. **`python scripts/shortify.py shorts/<slug>.json`** → narrates each line (plain
   `en-US-BrianNeural`), gets real per-word timings via **faster-whisper** on the audio,
   groups words into ≤4-word lines + auto-picks each line's keyword (longest non-stopword),
   stages stills/cover/music into `remotion/public`, writes a props JSON, and renders the
   Remotion `Short2` composition to `projects/<book>/shorts/<slug>.mp4`. `--no-render` stages only.
- `Short2` (`remotion/src/Short2.tsx`) is generic (all data from props via `--props`):
  persistent top-left badge, centre-safe karaoke captions (keyword ochre, spoken word
  scales), CSS crop-toward-subject, push-in. Duration from `calculateMetadata`.
- **Known minor polish:** whisper occasionally splits a hyphenated word ("push-up" → "PUSH
  -UP") or the longest-word keyword pick is weak ("EMBARRASSINGLY" over "SIMPLE") — eyeball
  each short; hand-edit the props JSON or spec if a line reads wrong. Rare mishears possible.

## Upload
Gate on the **parent video being PUBLIC** (a Short is a trailer; its "full verdict" link
must resolve). **Drip** 3–4 across the week+, don't dump. Same file → YouTube + TikTok +
Reels (the Higgsfield MCP can publish to TikTok). Link the long video in the description.

## Common mistakes
- **A debunk angle** ("your favorite X is fake") — reads smug in a format with no room to
  balance it. Teach a useful idea instead.
- **Captions in the bottom third** — hidden behind Shorts UI. Keep them dead-centre.
- **Estimated caption timing** — drifts out of sync. Use whisper word timings (shortify does).
- Slow Ken Burns as the *only* motion with no captions — dead. Karaoke carries the pace.
- Blind center-crop on an off-center subject — crops them out. Bias `pos` toward them.
- Shipping all ideas — weak Shorts are first impressions. Ship 3–4 strong, one idea each.
