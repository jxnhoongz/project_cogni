# Cognibot Script Redesign: the Story Architect

- **Date:** 2026-07-18
- **Status:** design approved; ready for implementation plan
- **Scope:** `cogni/script.py` (long mode) + a small tic-check extension + one config tweak. No change to images, narration, assembly, or the per-scene schema.

## Problem

Two independent model reviews of our four scripts (Claude and Kimi, in `script_review/`) converged on the same diagnosis — which matches the creator's felt symptom, *"I don't feel like I'm getting much from it."* The sentences are good; the **structure** is the disease:

1. **Every episode is the same shape.** Both reviews independently reconstructed the same ~9-step skeleton: cold-open on a capable person quietly failing → state the book's question → idea + praise → "honest gripe" → repeat → time-jump → "good for X, not Y" verdict → callback.
2. **The verdict is a summary in an opinion costume** — a hedged "good ideas, real caveats, modest outcome." Worse, the three finance videos deliver the *same* underlying take (privilege/luck) stamped on different books.
3. **The protagonist is a mannequin, not a character** — they *illustrate* each chapter's idea in order and all end "not rich / basically the same." Nothing is on trial, so the verdict is asserted, never earned.
4. **The verdict is given away by minute three** and dispensed in micro-doses, so nothing accumulates and the ending restates rather than lands.
5. **The "judging bot" voice never appears** — reads like any human YouTuber; the word "honest" is a verbal crutch.

**Root cause (confirmed in code):** `script.py`'s structure prompt hard-codes this skeleton — "Chapter 1 = cold open (the question); middle chapters each take one idea and *put the character through it* with an honest take; final chapter = outcome + verdict." The formula is written into the instructions. Prior fixes only *added rules* on top of that structure and did not stick.

## Goal & success criteria

Rebuild the generator so two principles are the **default architecture**, not bolted-on rules:
- **Test, don't illustrate** — the protagonist makes a real decision where the book's claim is wagered and *can lose*.
- **One book, one earned argument** — a single book-specific, defensible verdict, withheld and paid off.

**Tone:** "in-between" — real stakes plus a *light* wound for depth, while humor and usefulness stay dominant; intensity may vary per book. Protect what both reviews said works: the cold opens, the vivid prose, the push-back instinct, the protagonist device (reused as the *engine*, not the frame).

**Done =** the regenerated *Psychology of Money* script measurably fixes the reviews' specific complaints (see Validation).

## Design

### Architecture — two model passes (no extra model call)

The **Story Architect** pass *replaces* today's structure pass; the **Act Writer** pass is today's chapter pass, rewritten. Same number of model calls as now (the architect call carries a few more tokens than the old structure call — a rounding error).

1. **Story Architect** → a compact **Story Bible** (JSON).
2. **Act Writer** → dramatizes each act from the bible into beats.

The bible is stored on the document as `doc["story"]` so it is inspectable/editable and available to `script-review` later. Every downstream stage ignores unknown doc keys, so nothing breaks.

### Pass 1 — Story Architect → the Story Bible

Input: the outline (title, thesis, key ideas) — same input the structure pass gets today — plus the list of **prior story-shapes** used by other books (see Cross-video variety). Output JSON:

- `protagonist`: `{ name, description }` (recurring low-poly look, clear face, non-photorealistic) **plus** `wound` — one specific piece of history/shame that gives the character a reason to care, kept light per the in-between tone.
- `argument`: `{ stance: "mostly-right" | "mostly-wrong" | "dangerously-half-right", claim }` — one sentence someone could disagree with, *about this book specifically*. Withheld until the payoff.
- `wager`: `{ book_claim_on_trial, decision, outcome: "book-wins" | "book-loses" | "mixed" }` — a real decision with a downside; the book's advice is allowed (encouraged, sometimes) to lose.
- `plant` → `payoff`: one element set up early that detonates late.
- `closing_scene`: a single concrete final moment that embodies the argument (a scene, not a "who-it's-for" list).
- `opening_move`: the kind of cold open (must differ from prior books — not always "capable guy + flashy rival").
- `voice_moves`: 1–2 bot-only moves to deploy (total recall, catching the book contradict itself).
- `acts`: ordered list. Each act = `{ title, focus, role, ideas: [{ idea, mode: "tool" | "obstacle" | "failure" | "discovery" }], carries: "wager" | "plant" | "payoff" | "none" }`. Ideas may enter out of order. Acts map 1:1 onto the existing per-scene `chapter` field (name kept for schema compatibility).

### Pass 2 — Act Writer (rewritten chapter pass)

For each act, given the bible + the act spec + prior acts, write `min..max` beats that:
- **Dramatize, don't explain** — the character acts, decides, or discovers; replace narrator-lecture beats with **discovery beats** (the framework emerges from the character's friction/failure).
- Execute the `wager` / `plant` / `payoff` in the act the bible assigns it to; let the book win or lose per `wager.outcome`.
- **Withhold the verdict** — only the final act delivers the `argument` payoff. No "here's my verdict on this stretch" mid-roll summaries.
- Kill the credit→caveat→summary cycle and the "honest gripe" tic; cut the word "honest."
- Use the assigned `voice_moves`; keep the bot's blunt, funny register. (A bot "I read all 200 pages and caught the contradiction" claim is a factual assertion — the existing `fact-check` stage validates narration against `book.md`, so a fabricated contradiction gets flagged before narration.)
- Vary rhythm; do not read the act title aloud.

Per-beat output schema is unchanged: `narration`, `on_screen_text`, `image_prompt`.

### Cross-video variety (mechanical)

Today `_prior_protagonists()` feeds the writer the set of already-used names to force distinct protagonists. Extend this to **prior story-shapes**: scan other books' `doc["story"]` and collect their `argument.stance`, `opening_move`, and `wager.book_claim_on_trial` (theme). Hand these to the Story Architect with an instruction to pick a *different* stance and opening move. This makes the "every episode is the same" failure structurally impossible to repeat by default.

### Tic automation

Extend the existing `scripts/check_tics.py` family (runs before `narrate`, alongside the pronunciation check) to flag mechanically-detectable regressions:
- "honest"/"honestly" above a small per-script threshold.
- Fixed-skeleton phrases: "here's my honest take/gripe", "in this video", "who this is for", and time-jump stock phrases ("X years later", "months later") when they cluster.
These are reported for a rewrite pass, not auto-edited.

### Config

`config.yaml script.angle` currently nudges toward a house take (how the privilege critique became every finance video's default verdict). **Neutralize it:** repurpose the field to a stance-agnostic instruction — "form an earned, book-specific verdict; do not import a recurring house opinion" — rather than deleting it (avoids a config-shape change). The book-specific argument now comes from the Story Architect.

### Schema compatibility

`scenes.json` per-scene schema is identical. The only new data is `doc["story"]` (the bible). `script-review`, `visuals`, `review`, `narrate`, `images`, `animate`, and `assemble` are untouched and ignore the new key.

## Validation

Regenerate **The Psychology of Money** with the new system (`--force`; its `outline.json` exists), read old vs new, and check the reviews' specific complaints:
- Verdict is book-specific and *earned* by the story (not the privilege default)?
- A real wager exists where the book could lose?
- Skeleton broken — opening, sequence, and ending varied vs the other books?
- Middle uses discovery over lecture; the identified dead-spot patterns are gone?
- "honest" and the credit→caveat→summary tic dropped (tic check passes)?
- Ends on a concrete scene, not a "who-it's-for" list?
- A recognizable bot voice-move lands at least once?

If the architect's arc is weak, iterate the Story Architect prompt (it is the highest-leverage single prompt) before touching the Act Writer.

## Out of scope (YAGNI)

- No changes to images, narration, assembly, or the per-scene schema.
- No new review sub-stage that hard-depends on the bible; `script-review` *may* consume `doc["story"]` later, but that is not part of this work.
- **Short mode** (test-only, `script.mode: short`) is left as-is; this redesign targets **long mode** (production).
- The narration slow-down (~185 wpm) and the OpenRouter image regen are separately tracked and are not part of this spec.
