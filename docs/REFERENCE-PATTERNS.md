# What a channel we admire actually does

Structural teardown of a 16:30 Chinese breakdown of 《国富国穷》 (Landes, *The Wealth and
Poverty of Nations*) — transcribed with `scripts/transcribe.py`. Raw transcript lives in
`research/transcripts/` (gitignored; it isn't ours). This file is our own analysis.

Landes is the hardest possible density test: 600 pages of economic history, no
protagonist, no natural anecdote. If a format survives that, it survives anything.

## The measurements, against ours

| | Them (16:30) | Cognibot book #5 (21:30) |
|---|---|---|
| Distinct book ideas delivered | **~8** | **~4** |
| Words/min | **248** | 172 |
| Direct address ("you") | **4.6/min** | 2.2/min |
| Invented characters | **0** | 1 (carries 58% of runtime) |
| Time to a stated promise | **~2:00** | never |

They deliver roughly **twice the ideas in 5 fewer minutes**.

## The shape

- **0:00–0:45 — a cascade of concrete puzzles, in second person.** Why were *you* born
  speaking this language, eating rice and noodles, while someone across the world eats
  bread and steak? Why do *you* commute two hours for a mortgage while some countries
  work 30-hour weeks? Then it widens: why is Switzerland, with no coastline, among the
  richest countries? Each line is a curiosity gap. **The viewer is the protagonist.**
- **~1:00 — why this book, via the author.** Decades on one question; it detonated in
  economics because it said what Adam Smith left unsaid — Smith explained how wealth is
  *created* and dodged why it *accumulates in some places only*.
- **~2:00 — the explicit promise.** "His answer isn't one sentence, it's a whole model.
  Today I'll unpack it layer by layer, and afterwards you won't see rich and poor the
  same simple way again." A stated reason to stay.
- **3:00–13:00 — eight ideas, each ~60–90s, each with a hard concrete detail.**
  Tropical disease (no winter to kill pathogens; a farmer fighting three parasites is
  spending his body on survival, not accumulation) · navigable rivers as "highways the
  sky gave Europe" (a ton of freight at a tenth of Africa's cost) · Protestantism and
  time-as-God's-gift producing clocks, factory shifts, the assembly line · China's
  high-level equilibrium trap (too good at squeezing yield from existing fields to need
  a machine) · Spain's resource curse · English kings too broke to avoid Parliament, so
  property rights got bargained into existence · patent law finally tying knowledge to
  money · corruption as the vicious cycle where effort stops paying.
- **13:00–15:00 — where the book is now WRONG.** An explicitly signposted section: Landes
  wrote before modern China, so here is what he could not see. This is the same move as
  our Kahneman replication beat — the "I know what happened after publication" card,
  and they save it for the payoff position.
- **15:00–16:30 — the verdict, then buy the book.** Their own thesis (nations that
  recover from a hundred mistakes beat nations undone by one; that self-repair capacity
  is what matters), the book reframed as "a map, not a book of answers", and a CTA to
  **buy the book** — not to subscribe.

## What this settles for us

1. **No invented protagonist. Not one, in 16 minutes, on a book with no human story.**
   The device we treat as our core differentiator is absent from the format we're
   imitating, on the hardest possible material for going without it.
2. **The viewer is the protagonist instead.** Second person from word one, at 2× our
   rate. It costs nothing and needs no fiction. Our beat 1 is "This is Priya" — a
   stranger, third person, and the audience is a spectator to someone else's grief.
3. **Density is the product.** ~8 ideas vs our ~4, in less time.
4. **The hook is a puzzle cascade, not a story.** Open loops made of facts.
5. **Front-load the QUESTION and the PROMISE — not the verdict.** This corrects earlier
   advice in this repo's history: they do *not* state their judgment early. They state
   the question, promise a model, and hold the verdict for 15:00. What was missing from
   ours was never an early verdict; it was an early *reason to stay*.
6. **"Where the book is outdated" belongs near the end** as the payoff, which is exactly
   where book #3's replication beat sat — our best moment, arrived at by accident.

## Cheap changes this implies

- Narration rate: they run 248 wpm, Brian runs ~167 at default. `tts.rate: "+12%"`
  gets ~190 without re-scripting, and buys room for more ideas per minute.
- Second person as a script constraint, measurable (`you`/min) like our other gates.
- An idea-coverage gate: `ingest` already extracts ~12 key ideas; count how many the
  final script actually delivers. Book #5 delivered 7, three of them the same contrast.

---

# 成长书库 — 《牛奶可乐经济学》 (33:20) — the closest peer

Second teardown. This is the channel the user calls "basically ours but Chinese," at
nearly our runtime (33:20 vs our v2 26:45). Full script: `research/transcripts/
chengzhang_ref01_SCRIPT.md`. The user watched the whole thing and it held their interest —
so the job here is to find WHY, structurally, and adopt it.

## The architecture: a fractal of puzzle-chains

The whole 33 min is **7 sections**, each with the IDENTICAL internal shape:

    3-4 concrete puzzles  →  each puzzle: "why is X?" then the economic principle
                          →  section SYNTHESIS (one line tying the examples together)
                          →  BRIDGE to next section (synthesize + escalate + re-hook)

Sections, in order — note the scope moving steadily INWARD:
1. **Product design** (0:42) — milk box vs coke bottle, fridge light, shirt buttons
2. **"Free" traps** (6:00) — bar peanuts, bundled software, "no receipt = free meal"
3. **Your wages** (11:18) — model pay, waiter vs chef, low-performers overpaid
4. **Price discrimination** (15:53) — hidden Starbucks cup, dented appliances, hotel wifi
5. **Involution / commons** (20:21) — high heels, school uniforms, cherry tree, antibiotics
6. **Information games** (24:54) — used-car lemons, lawyers' luxury cars, academic jargon
7. **Your own irrationality** (30:04) — splitting the bill, taxi drivers quitting in rain

Objects "out there" → you as consumer → your income → your society → your own mind. The
final section turns the lens on the viewer. That escalation is the spine.

## The 5 techniques worth stealing (ranked)

1. **PUZZLE DENSITY. ~22 puzzles in 33 min — one "why?" every ~90 seconds.** Every single
   idea enters as a concrete anomaly ("why is milk square but coke round?") and only THEN
   gets the principle. Never definition-first, not once in 33 minutes. This is the engine
   of the whole thing. Our v2 anchors ideas on facts — this goes further: the anchor is a
   QUESTION the viewer can't answer, posed before the idea.

2. **EXPLICIT SECTION TRANSITIONS that do three jobs at once** (there are 6, ~every 5 min):
   synthesize what just happened in one line, ESCALATE ("if you think calculating product
   cost is clever, you underestimate them — they don't just calculate products, they
   calculate YOU"), then pose the next section as a cliffhanger. This is the "suspension
   bridge / open loop" retention move, done deliberately at every seam. It's the single
   biggest reason a 33-min video doesn't sag.

3. **THE HOOK'S PUZZLES PAY OFF FAST.** The cold open poses 3 (milk/coke, buttons, bar
   peanuts); milk/coke + buttons are answered within §1, peanuts opens §2. The viewer gets
   closure in the first ~5 min — that earned trust is what buys the next 28.

4. **ESCALATING INWARD SCOPE** (the section order above). Not 7 parallel topics — a
   widening/deepening lens ending on the viewer's own mind. Gives a 33-min video an arc.

5. **RE-ANCHORING at each section start.** Every section opens by recapping the previous
   one in a sentence before starting ("last part we dissected the price traps; now...").
   For a long video a drifting viewer can re-board. (Theirs is near-verbatim repetition —
   a stitched-segment tell; we'd do a lighter one-line version.)

## What we already do (v2)

Second person, concrete anchors, no invented characters, ideas each on a fact. The format
rewrite got us onto the same road. The gap is the DENSITY and the TRANSITIONS above.

## The one thing they DON'T do — and it's our differentiator

**They never judge the book.** The conclusion is celebratory ("this book gives you x-ray
vision"), never critical — no "here's where it's wrong" section. That's the 成长书库 =
summary-channel signature: brilliant organization, zero adversarial stance. The user found
it engaging anyway, which proves the engagement comes from STRUCTURE, not from a verdict.
So: adopt their puzzle-chain engine AND keep Cognibot's verdict + `where-the-book-is-wrong`
act. Structure for retention, verdict for differentiation. We can be both.

## Concrete pipeline changes (for `cogni/script.py` architect)

- **Add a `puzzle` field per idea** alongside `anchor`: the "why is X?" question that opens
  it. Make the act writer LEAD with the puzzle, then answer. Target ~one puzzle/90s.
- **Make section transitions a first-class thing.** Each act should END on a synthesize +
  escalate + next-question bridge, and OPEN with a one-line recap. Add `bridge_out` to the
  act schema; it's currently implicit and inconsistent.
- **Order acts by escalating scope** where the material allows — outward objects to the
  viewer's own mind — and say so in the architect prompt.
- Keep `where-the-book-is-wrong` + `verdict`. Their absence is exactly our edge.
