import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";
import { Short, Narr, Shot } from "./Short";
import { CREAM } from "./theme";

// --- Pilot Short: Atomic Habits, "the 37x is a calculator trick" (puzzle-first) ---
// Two tracks. NARRATION runs continuous; VISUALS cut every ~2-4s over the top.
// Studio-preview default. These asset names are what scripts/shortify.py stages from
// shorts/atomic-habits-37x.json — run `python scripts/shortify.py shorts/atomic-habits-37x.json
// --no-render` to (re)populate remotion/public for the preview. Real renders pass their own
// spec via --props, so this block is only the interactive default.
const P = "atomic-habits-37x";
const AH_NARR: Narr[] = [
  { src: `${P}_beat_1.mp3`, dur: 12.12 }, { src: `${P}_beat_2.mp3`, dur: 6.62 },
  { src: `${P}_beat_3.mp3`, dur: 11.52 }, { src: `${P}_beat_4.mp3`, dur: 10.58 },
  { src: `${P}_beat_5.mp3`, dur: 11.3 }, { src: `${P}_beat_6.mp3`, dur: 6.36 },
];
const AH_SHOTS: Shot[] = [
  { kind: "hook", dur: 3.2, cap: ["1% A DAY", "= 37× A YEAR?"] },
  { kind: "photo", img: `${P}_s004.png`, pos: "62% 50%", dur: 3.3, cap: ["THE FAMOUS", "PROMISE"] },
  { kind: "photo", img: `${P}_s029.png`, pos: "50% 48%", dur: 3.0, cap: ["1% BETTER", "EVERY DAY"] },
  { kind: "photo", img: `${P}_s026.png`, pos: "68% 48%", dur: 2.62, cap: ["THE QUESTION", "NOBODY ASKS"] },
  { kind: "photo", img: `${P}_s016.png`, pos: "70% 45%", dur: 3.2, cap: ["SO WHY DOESN'T", "ANYONE?"] },
  { kind: "photo", img: `${P}_s022.png`, pos: "68% 45%", dur: 3.42, cap: ["END UP 37×", "BETTER?"] },
  { kind: "photo", img: `${P}_s020.png`, pos: "72% 50%", dur: 3.26, cap: ["HERE'S THE MATH"] },
  { kind: "photo", img: `${P}_s021.png`, pos: "68% 45%", dur: 4.0, cap: ["1.01 ^ 365"] },
  { kind: "photo", img: `${P}_s020.png`, pos: "72% 50%", dur: 4.26, cap: ["A CALCULATOR.", "NOT A STUDY."] },
  { kind: "photo", img: `${P}_s029.png`, pos: "50% 48%", dur: 3.54, cap: ["BUT THIS PART", "IS REAL"] },
  { kind: "photo", img: `${P}_s017.png`, pos: "60% 45%", dur: 3.5, cap: ["SMALL CHOICES", "AREN'T NEUTRAL"] },
  { kind: "photo", img: `${P}_s019.png`, pos: "42% 50%", dur: 3.54, cap: ["UP OR DOWN.", "EVERY DAY."] },
  { kind: "photo", img: `${P}_s034.png`, pos: "50% 42%", dur: 3.46, cap: ["THE SHARPEST", "IDEA"] },
  { kind: "photo", img: `${P}_s032.png`, pos: "60% 48%", dur: 3.7, cap: ["DON'T WANT IT", "MORE—"] },
  { kind: "photo", img: `${P}_s031.png`, pos: "50% 42%", dur: 4.14, cap: ["BECOME THE TYPE.", "NOT THE OUTCOME."] },
  { kind: "photo", img: `${P}_s037.png`, pos: "50% 45%", dur: 2.86, cap: ["ONE HOLDS UP.", "ONE DOESN'T."] },
  { kind: "end", dur: 3.58, cap: ["FULL VERDICT", "ON THE CHANNEL"] },
];

// The active book's acts, in order — these must match scenes.json `chapter` values,
// since finalize.py places Ch{n}.mov at each act's first beat (Ch1 skipped by default
// so the card doesn't cover the hook).
// PER-BOOK KNOBS — retarget BOTH of these together when the active book changes.
// The intro title used to be hardcoded inside Intro.tsx, which is how book #5 shipped
// a cut that opened with book #4's title card.
const BOOK_TITLE = "THE RICHEST MAN IN BABYLON";
const BOOK_AUTHOR = "George S. Clason";

const CHAPTERS = [
  "The City With No Gold",
  "The Seed You Never Plant",
  "Glass That Looked Like Jewels",
  "Clay Tablets and Stone Walls",
  "Luck You Build With Your Hands",
  "The Chapter Clason Couldn't Write",
  "Keep the Tenth, Burn the Fairy Tale",
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Intro" component={Intro} durationInFrames={180} fps={30} width={1920} height={1080}
        defaultProps={{ bookTitle: BOOK_TITLE, author: BOOK_AUTHOR, cover: "book_cover.jpg" }} />
      <Composition id="Outro" component={Outro} durationInFrames={210} fps={30} width={1920} height={1080} />
      {CHAPTERS.map((title, i) => (
        <Composition
          key={i}
          id={`Ch${i + 1}`}
          component={JuiceChapter}
          durationInFrames={120}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ index: i + 1, title }}
        />
      ))}
      <Composition
        id="Countup"
        component={JuiceCountup}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
        // Lands on beat 71 — the Dow lost ~89% from its 1929 peak to the 1932 trough
        // (web-verified). THE number the book's "gold always multiplies" fairy tale
        // defines away — it hit the patient saver and the gambler alike.
        defaultProps={{ value: 89, prefix: "", suffix: "%", kicker: "the Dow, 1929 → 1932", sub: "gone — saver and gambler alike", ink: CREAM }}
      />
      <Composition id="JuiceDemo" component={JuiceDemo} durationInFrames={750} fps={30} width={1920} height={1080} />
      {/* Generic vertical-Short composition. Per-short data comes from a spec JSON via
          `--props` (scripts/shortify.py writes it); AH is the Studio-preview default.
          calculateMetadata derives the length from the shot durations, so every short
          renders at its own runtime with no per-short Root edit. */}
      <Composition id="Short" component={Short} fps={30} width={1080} height={1920}
        defaultProps={{ narr: AH_NARR, shots: AH_SHOTS, music: "ah_music.mp3" }}
        calculateMetadata={({ props }) => ({
          durationInFrames: (props.shots as Shot[]).reduce((s, b) => s + Math.round(b.dur * 30), 0),
        })} />
      {/* Thumbnails for the ACTIVE book (Man's Search for Meaning). Backgrounds live in
          remotion/public/ — copy the chosen scene stills there before rendering.
          Keep each line under ~12 chars: 128px type overflows 1280 wide past that. */}
      {/* Must read COLD. "SUFFER CORRECTLY." on book #5 only parsed if you'd already
          watched the video — a payoff phrase, not a promise. Test each line against:
          would a stranger scrolling past understand what this video claims? */}
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "rmb_crash.png", line1: "He preached rich.", line2: "He went broke.", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "rmb_tenth.png", line1: "Keep the tenth.", line2: "Burn the rest.", side: "left" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "rmb_hook.png", line1: "Save for years.", line2: "Still broke?", side: "right" as const }} />
    </>
  );
};
