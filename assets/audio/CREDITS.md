# Background music — attribution

All tracks in this folder are Kevin MacLeod (incompetech.com), licensed
**Creative Commons Attribution 4.0** (CC BY). The licence REQUIRES a credit in the
video description — `assemble` picks a track per book automatically, so check which
one landed (`[assemble] mixing music: <file>`) and paste that track's line below into
the description.

Standard credit line (substitute the track name):

> "<Track Name>" by Kevin MacLeod (incompetech.com)
> Licensed under Creative Commons: By Attribution 4.0 — https://creativecommons.org/licenses/by/4.0/

| File | Track name | Mood |
|---|---|---|
| `almost_new.mp3` | Almost New | mellow |
| `at_rest.mp3` | At Rest | calm piano |
| `backbay_lounge.mp3` | Backbay Lounge | lounge jazz |
| `bittersweet.mp3` | Bittersweet | mellow |
| `carefree.mp3` | Carefree | light folk, upbeat |
| `deadly_roulette.mp3` | Deadly Roulette | jazz-noir (crime/econ books) |
| `deliberate_thought.mp3` | Deliberate Thought | pensive piano |
| `dreams_become_real.mp3` | Dreams Become Real | soft piano |
| `floating_cities.mp3` | Floating Cities | melancholy piano |
| `frozen_star.mp3` | Frozen Star | spacey ambient |
| `gymnopedie_no_1.mp3` | Gymnopedie No 1 | classical (Satie) |
| `healing.mp3` | Healing | gentle |
| `heartbreaking.mp3` | Heartbreaking | emotional piano (short 1:36 — loops a lot) |
| `immersed.mp3` | Immersed | ambient |
| `lobby_time.mp3` | Lobby Time | light jazz |
| `long_note_two.mp3` | Long Note Two | ambient drone |
| `thinking_music.mp3` | Thinking Music | quirky pensive |
| `wholesome.mp3` | Wholesome | warm folk |
| `windswept.mp3` | Windswept | airy ambient |

Used so far: Healing (book #1), Long Note Two (book #4), Thinking Music (book #5),
Deliberate Thought (book #6 Freakonomics).

**Not music:** `outro_vo.mp3` is the narrated outro line, kept here as the SOURCE for
muxing into `remotion/out/outro.mp4` (a fresh Remotion render of Outro has NO audio —
re-mux this after re-rendering or the sign-off goes silent). The auto-picker skips
`*_vo` files.

**Library growth re-rolls the hash:** the auto-pick is `sha1(slug) % len(tracks)`, so
adding tracks changes what a RE-assemble of an old book would pick (and thus its
required attribution line). Already-rendered videos are unaffected; if you re-assemble
an old book, re-check `[assemble] mixing music:` and fix the credit.

**Pixabay:** more beds can be hand-downloaded from pixabay.com/music (Pixabay Content
License — free for monetized YouTube, no attribution required, but note the source +
track here anyway). Downloads must be manual (their ToS forbids scripted scraping);
drop files in this folder, snake_case names, and they join the auto-pick pool.

> Track names here are derived from the filenames, which were taken from the
> Incompetech downloads. Before publishing, confirm the exact title and licence
> version on incompetech.com — CC BY credit is a licence condition, not a courtesy.
