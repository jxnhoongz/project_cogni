# Motion notes — Seedance via Higgsfield

Distilled (cherry-picked) from **smixs/visual-skills** (`video/references/seedance.md`
and `camera-lighting-vocabulary.md`), adapted to Cogni's **contemplative still-life**
style: Risograph, no faces/hands, single subject, one calm move. We deliberately do
NOT use that skill's dramatic machinery (character-locking, multi-shot cuts, dialogue,
emotional micro-actions) — wrong genre for us.

## Why the first clips barely moved (three causes, all fixable)
1. **Identical keyframes** — `end_image_prompt` was "the same scene a moment later,
   one subtle change", so start ≈ end and there's nothing to interpolate.
2. **Stasis words** — `video_prompt` said "no camera shake", "static", "still",
   "barely perceptible" — literally instructing Seedance to freeze.
3. **Sub-5s clips** — Seedance ignores motion below 5s; we used 4s.

## Rules for `video_prompt` (the `visuals` stage must follow these)
- **Describe ONLY the motion, not the still.** Seedance's own rule: "when using a
  reference image, do NOT describe elements already visible in the image" — re-describing
  the picture causes drift and dampens motion. So no "the alarm clock, the Risograph
  look…" — just the camera/motion.
- **Use a real camera move** from the vocabulary below. Ban "gentle drift", "no camera
  shake", "static", "still", "barely perceptible".
- **One slow move per clip** — calm and cinematic, fits our tone.
- **Clips ≥ 5–6s** (5s minimum for motion to register; 15s max on Seedance 2.0).

## Motion method — Option B (chosen)
**Single start frame + a camera-move prompt.** Drop the near-identical end frame.
Two-keyframe start→end is for real transformations; our still-lifes aren't. Bonus: no
end-frame image = ~half the image cost.

## Camera-move vocabulary (Seedance-friendly, calm end of the range)
`slow push-in` (dolly-in) · `slow pull-back` (dolly-out) · `pan left/right` ·
`tilt up/down` · `lateral tracking` · `slow orbit` · `gimbal glide` · `parallax` ·
`rack focus`. Avoid the aggressive ones for our tone: whip pan, snap zoom, handheld shake.

## Length & beats (covering long narration)
- Narration averages ~20s/scene; one clip caps at 15s.
- **Beats:** split a scene into ~2 clips of ~8–12s, each its own slow move, concatenated
  in order — **never looped**.
- Cost ≈ **3.5 credits/sec** (Seedance 2.0, 720p, fast). A fully-animated ~20s scene ≈
  70 credits. Scenes we don't fully animate: still + Ken Burns fills any length natively.

## Never
Never loop a short clip to fill a long scene (the "pop"). Play once → hold the last frame
with Ken Burns, or use beats.
