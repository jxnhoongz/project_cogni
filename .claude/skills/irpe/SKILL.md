---
name: irpe
description: Use before changing code — before the first Edit/Write, running a build, or starting any fix or feature. Triggers when you catch yourself about to edit, when a task "looks like a one-liner", when you're in a hurry, or the moment you reach for a file before you've named what the change touches.
---

# IRPE — plan before you build

**Investigate → Radius → Plan → Execute.** Four gates, in order. You do not open an
editor or run a build until **I**, **R**, and **P** are done — even for a "trivial"
change. Jumping to Execute is the exact failure this prevents.

**Skipping a phase (the letter) is skipping IRPE (the spirit).** "I did it in my head"
is skipping — the point is to make it explicit.

## The four phases

### I — Investigate
Understand the ACTUAL problem and the CURRENT code before touching anything.
- Reproduce/confirm the problem — don't fix from a guess.
- Read the real file(s) you'll change **and** the ones next to them. Confirm you're in
  the right place (right repo, branch, module — this is where "editing the wrong file"
  happens).
- Find existing helpers/patterns to **reuse** instead of reinventing.
- **Output:** one or two sentences — the real problem + its root cause.

### R — Radius   ← the step that gets skipped
Name the blast radius **in writing**, not in your head. This is IRPE's whole point.
- Which files/functions will the change touch?
- **Who calls the thing you're changing?** grep the callers. Does its signature or
  behavior change for them?
- What downstream stages, data, or outputs depend on it? What could break?
- **Output:** a written list — affected files + callers + downstream effects.

### P — Plan
The concrete approach, before any edit.
- What changes in each file, in what order; which helpers from **I** you reuse; the edge
  cases; and **how you'll verify** (the test or observation that proves it works).
- **Output:** a few bullets. Short is fine — written is the requirement.

### E — Execute
Only now edit. Follow the plan, then verify the way **P** said you would.

## The gate
Reaching for Edit / Write / a build command before I·R·P exist on the page? Stop —
that's the move IRPE exists to catch. Back up to Investigate.

## Quick reference
| Phase | Question | Output |
|---|---|---|
| **I**nvestigate | What's really wrong, and what does the current code do? | root cause + files read |
| **R**adius | What does this touch, and who/what depends on it? | affected files + callers + downstream |
| **P**lan | How, in what order, reusing what, verified how? | short written plan |
| **E**xecute | (build it) | the change + verification |

## Rationalizations — all mean STOP, back up
| Excuse | Reality |
|---|---|
| "It's a one-liner." | One-liners still have callers and downstream. 60s of Radius beats an hour of rework. |
| "I already know this code." | You knew it last month; it moved. Read it now — and confirm the file/branch. |
| "Planning is slower." | Unplanned edits cause re-edits. Plan-first is faster end to end. |
| "I'll scope it as I go." | Scoping mid-edit = discovering the breakage after you shipped it. |
| "The radius is obvious." | Then writing it costs 20 seconds — and the obvious one is hiding a caller. |
| "We're in a hurry." | Hurry is when skipped Radius bites hardest. Do I·R·P *fast*; don't skip. |

## Red flags — you're mid-skip
- Opening an editor before you've **named the affected files**.
- "Let me just quickly change…"
- Grepping the thing you'll change but not its **callers**.
- No sentence stating the **root cause**.
- Starting to edit because the clock is ticking.

Any of these → back up to **Investigate**.
