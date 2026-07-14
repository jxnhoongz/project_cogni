# Cognibot Narration Redesign — Design

- **Date:** 2026-07-14
- **Status:** Brainstorm approved → pending spec review
- **Branch:** `claude/cognibot-redesign`

## Problem

Three issues surfaced from reviewing `test_high.mp4`:

1. **Image/narration mismatch.** A scene is 3–6 sentences but carries ~1 image, so the
   picture doesn't track what's being said. Scene 3 narrates "we call our car and our
   house 'investments'…" (a *liability* point) while the screen shows the *asset* image
   (a fruit tree). The viewer notices.
2. **Narration is verdict-essay, not teaching.** The channel is **Cognibot** (banner:
   "my human lazy, me read book for human"). The narrator should *teach* the book's
   concepts/lessons/verdicts by telling a **relatable story**, not deliver an abstract
   essay.
3. **Subtitles look bootleg.** White text on a hard semi-transparent black box — clashes
   with the Risograph art.

## Identity / persona (locked in brainstorm)

- **Narrator = Cognibot**: a bot that read the book so a lazy human doesn't have to.
  Talks **normally** (the pidgin lives on the channel banner only), blunt, a little
  funny, and **judges as it goes**.
- **Voice = `en-US-BrianMultilingualNeural`** (Brian) via edge-tts — casual, natural,
  "real person talking to you." (Chosen by ear from a 11-voice audition.)
- **Structure = one invented protagonist per book** whose story carries the lessons.
- **Verdict integration = story teaches, Cognibot judges, woven throughout** — not saved
  for a final act, not silent show-don't-tell. This is how "verdict, not summary"
  (the project's identity) survives inside a story.
- **Register = natural clear English.** Personality lives in *content* (blunt takes,
  "I read it for you"), not in an accent.

## Design

### A. Script agent (`cogni/script.py`) — the core rewrite

- **Invents a relatable protagonist** fitting the book's domain (finance → "Ana," broke
  on a good salary; another book gets a different character), with a clear arc:
  - **Cold open:** her relatable problem, framed as the question the book promises to
    answer — no verdict yet.
  - **Body:** she runs into each key idea from `outline.json`; Cognibot *teaches* the
    idea through what happens to her, then *steps out to judge the book* — what it nails,
    what it skips, who it fails.
  - **Close:** her outcome + the earned overall verdict + who it's actually for.
- **Beat granularity — one beat = one scene = one image.** The agent writes **short
  beats**: each scene is a single visual moment (~1–2 sentences, ~5–10s spoken) with an
  `image_prompt` that shows exactly that moment. A ~30-min video becomes ~120–160 short
  scenes instead of ~13 long ones.
- **Character consistency.** Art is silhouette / no-face, so the protagonist stays
  consistent as a recurring silhouette. Add a **doc-level `character`** field (name +
  short visual description) the agent writes once; every beat's `image_prompt` is asked
  to honor it ("the same figure…").
- Keeps the **per-scene `scenes.json` schema** (narration / on_screen_text /
  image_prompt) — finer-grained, not structurally different, so downstream stages are
  unaffected. Both `short` and `long` modes adopt this.

### B. Sync — one beat = one scene = one image

- Falls directly out of A. Every downstream stage already runs per-scene, so it works
  unchanged, and the mismatch becomes **structurally impossible** — each image is minted
  for its own sentence.
- **Trade-off:** ~150 images/video (~$6 in image gen at ~$0.04/image; images cache) and a
  snappier, more-cutting feel. Accepted.

### C. LOW / MEDIUM / HIGH per beat (the motion dial)

- New per-scene **`mode`** field. A tagging step (a small new stage, or folded into
  `visuals`) rates each beat:
  - **LOW** = still + very slow Ken Burns pan. **ffmpeg only, FREE**, no Higgsfield.
  - **MEDIUM** = **Higgsfield**, *restrained* — one calm element moves / a gentle push;
    short clip (~5–6s). Costs credits, modestly.
  - **HIGH** = **Higgsfield**, full treatment — bigger/compound camera moves + element
    motion, optionally two-clip (setup→reveal) beats, connected & lively (as in
    `test_high.mp4`); longer clips; reserved for the biggest beats.
- **Both MEDIUM and HIGH spend Higgsfield; LOW is the only free tier.** The dial controls
  *how many* beats get MEDIUM/HIGH — a budget lever. Guidance: most beats LOW, a handful
  MEDIUM, a few HIGH (≈6–12 animated beats in a 30-min video).

### D. Assemble (`cogni/assemble.py`)

- **Mode-aware rendering:** LOW → Ken Burns still; MEDIUM/HIGH → play the clip then
  hold/drift the final frame; **dissolve between scenes** (productionize the `test_high`
  learnings: `xfade` + `acrossfade`, Ken-Burns tail on the held reveal frame).
- **Subtitle restyle (Riso):** cream text (~`#F1EDE4`), a soft semi-transparent
  dark-teal backing (or a gentle shadow instead of a hard box), a cleaner font,
  lower-third with breathing room. Exact look **approved via a rendered preview frame**
  during build. Driven by a config style block.

### E. Config (`config.yaml`)

- `tts.voice: en-US-BrianMultilingualNeural`.
- New **subtitle style** settings (text color, backing, font, position) in the `video`
  block.
- **Mode** settings (available modes; default budget/target counts for MEDIUM/HIGH).

### F. Reviews (`script_review.py`, `fact_review.py`)

- Adapt prompts to the new voice/story (still flag weak narration; still ground claims
  against `book.md`). Mechanics unchanged.

### G. Skills & docs cleanup (prevent agent hallucination)

The `.claude/skills/` set is split between the current pipeline and **pre-pivot relics**
from the abandoned "cognilab / 认知提升" Chinese-shorts era. The relics reference tooling
and paths that **do not exist** (DALL·E oil paintings, Whisper captions, `scripts/*.sh`,
`cognilab/catalog/books.json`, shorts, 7-day-experiment chapters). Because their
descriptions say things like "use after every script generation," an agent will invoke
them and run non-existent scripts / wrong styles.

- **Delete (stale, pre-pivot):** `asset-librarian`, `book-catalog-manager`,
  `copyright-compliance-checker`, `midform-script-generator`, `script-quality-checker`,
  `video-renderer`. (git history preserves them.)
- **Update (redesign changes them):**
  - `cogni-animate` — rewrite for **LOW / MEDIUM / HIGH** modes (MEDIUM/HIGH = Higgsfield,
    LOW = free ffmpeg); drop the "animate every scene" framing; align with mode tagging
    and the beat structure.
  - `docs/motion.md` — add the LOW/MEDIUM/HIGH vocabulary; keep the Seedance/camera guidance.
- **Keep as-is:** `irpe` (discipline skill), `docs/STYLE.md` (current Risograph STYLE token).

This cleanup lands in **Phase 1** (deletions + a stub note) so no stale skill can misfire
during the rebuild; `cogni-animate`/`motion.md` updates land with **Phase 3** (modes).

## Non-goals

- No change to `ingest` / `outline.json`.
- No change to the image provider or the art STYLE token.
- No premium TTS provider yet (edge/Brian is enough; pluggable later per existing design).

## Phasing (validate cheap → scale)

1. **Phase 1 — voice + story + subtitles.** Rewrite `script.py` (Cognibot + character
   story, `short` mode first), set `voice = Brian`, restyle subtitles. Regenerate the
   Rich Dad *short* script → listen/watch. Validates the creative pivot before scaling.
2. **Phase 2 — beat granularity.** Tighten the script to one-beat-per-scene; confirm
   image/narration sync on a few scenes (no car/tree mismatch).
3. **Phase 3 — modes + assemble.** Add LOW/MEDIUM/HIGH tagging + mode-aware assemble +
   dissolves (productionize the `test_high` pipeline). Spend Higgsfield only on tagged
   beats, always behind the `cogni-animate` cost-quote guardrail.

Each phase can be its own `writing-plans` implementation plan; we start with Phase 1.

## Verification

- **Phase 1:** regenerated short script reads as Cognibot *teaching a story + verdicts*;
  TTS renders in Brian; subtitle preview frame approved by the user.
- **Phase 2:** pick 3 beats, confirm each image matches its sentence.
- **Phase 3:** render a 3-beat mix (LOW + MEDIUM + HIGH) with dissolves; confirm each mode
  renders and transitions are smooth; **cost quoted and approved before any Higgsfield
  spend** (cogni-animate guardrail).

## Risks

- **150-scene scripts:** longer generation, more images. Mitigate with caching and phase
  gating.
- **Forced character:** invented protagonists could feel fake for non-narrative books.
  Mitigate: the script prompt lets the "character" be a light representative everyperson,
  not a heavy fictional arc, when the book resists story.
- **Beat length vs Higgsfield minimum (≥5s):** size MEDIUM/HIGH beats to ≥5s; keep very
  short beats LOW.
