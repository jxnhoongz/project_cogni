import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";
import { Short2, Seg } from "./Short2";
import { CREAM } from "./theme";

// --- Short v2: Atomic Habits, IDENTITY (teach-not-dunk). Kinetic centre captions +
// persistent top-left book badge. Chunk timings from scripts (edge-tts durations). ---
// Studio-preview default only. Real shorts pass their own spec JSON via --props
// (scripts/shortify.py writes it: narrate -> whisper word timings -> keyword lines).
const AH2_SEGS: Seg[] = [
  { dur: 6.14, img: "short2_s016.png", audio: "short2_seg_1.mp3", lines: [{k:1,ws:[{w:"YOUR",t:0.0},{w:"HABITS",t:0.2},{w:"DON'T",t:0.48},{w:"STICK",t:0.86}]},{k:3,ws:[{w:"AND",t:1.92},{w:"IT'S",t:2.06},{w:"NOT",t:2.24},{w:"BECAUSE",t:2.4}]},{k:1,ws:[{w:"YOU'RE",t:2.76},{w:"LAZY",t:3.0}]},{k:1,ws:[{w:"IT'S",t:3.92},{w:"BECAUSE",t:4.06},{w:"OF",t:4.22},{w:"WHO",t:4.52}]},{k:1,ws:[{w:"YOU",t:4.74},{w:"THINK",t:4.88},{w:"YOU",t:5.08},{w:"ARE",t:5.32}]}] },
  { dur: 6.86, img: "short2_s029.png", audio: "short2_seg_2.mp3", lines: [{k:1,ws:[{w:"THE",t:0.0},{w:"SHARPEST",t:0.18},{w:"IDEA",t:0.6},{w:"IN",t:0.94}]},{k:0,ws:[{w:"ATOMIC",t:1.28},{w:"HABITS",t:1.5}]},{k:1,ws:[{w:"EVERY",t:2.7},{w:"ACTION",t:3.22},{w:"YOU",t:3.54},{w:"TAKE",t:3.86}]},{k:2,ws:[{w:"IS",t:4.04},{w:"A",t:4.26},{w:"VOTE",t:4.38},{w:"FOR",t:4.6}]},{k:3,ws:[{w:"THE",t:4.92},{w:"TYPE",t:5.04},{w:"OF",t:5.24},{w:"PERSON",t:5.42}]},{k:1,ws:[{w:"YOU'RE",t:5.68},{w:"BECOMING",t:5.94}]}] },
  { dur: 4.58, img: "short2_s037.png", audio: "short2_seg_3.mp3", lines: [{k:2,ws:[{w:"SO",t:0.0},{w:"DON'T",t:0.2},{w:"SET",t:0.48},{w:"A",t:0.64}]},{k:0,ws:[{w:"GOAL",t:0.76},{w:"TO",t:0.98},{w:"RUN",t:1.24},{w:"A",t:1.44}]},{k:0,ws:[{w:"MARATHON",t:1.56}]},{k:3,ws:[{w:"SET",t:2.58},{w:"OUT",t:2.78},{w:"TO",t:2.98},{w:"BECOME",t:3.24}]},{k:1,ws:[{w:"A",t:3.44},{w:"RUNNER",t:3.72}]}] },
  { dur: 4.15, img: "short2_s044.png", audio: "short2_seg_4.mp3", lines: [{k:3,ws:[{w:"DON'T",t:0.0},{w:"TRY",t:0.32},{w:"TO",t:0.5},{w:"WRITE",t:0.68}]},{k:1,ws:[{w:"A",t:0.9},{w:"BOOK",t:1.02}]},{k:2,ws:[{w:"BE",t:1.92},{w:"A",t:2.02},{w:"WRITER",t:2.14},{w:"ONE",t:2.36}]},{k:1,ws:[{w:"PAGE",t:2.78},{w:"TODAY",t:3.12}]}] },
  { dur: 5.78, img: "short2_s031.png", audio: "short2_seg_5.mp3", lines: [{k:2,ws:[{w:"CHANGE",t:0.0},{w:"THE",t:0.32},{w:"IDENTITY",t:0.62}]},{k:2,ws:[{w:"AND",t:1.54},{w:"THE",t:1.76},{w:"HABIT",t:1.88},{w:"STOPS",t:2.1}]},{k:1,ws:[{w:"NEEDING",t:2.48},{w:"WILLPOWER",t:2.86}]},{k:1,ws:[{w:"IT'S",t:4.08},{w:"JUST",t:4.28},{w:"WHO",t:4.44},{w:"YOU",t:4.64}]},{k:0,ws:[{w:"ARE",t:4.8},{w:"NOW",t:4.98}]}] },
  { dur: 4.18, img: null, audio: "short2_seg_6.mp3", lines: [{k:3,ws:[{w:"THAT'S",t:0.0},{w:"THE",t:0.32},{w:"IDEA",t:0.42},{w:"WORTH",t:0.64}]},{k:0,ws:[{w:"STEALING",t:0.98}]},{k:2,ws:[{w:"THE",t:2.1},{w:"FULL",t:2.16},{w:"VERDICTS",t:2.36},{w:"ON",t:2.98}]},{k:1,ws:[{w:"THE",t:3.16},{w:"CHANNEL",t:3.28}]}] },
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
  "Keep the Tenth, Skip the Fairy Tale",
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
      <Composition id="Short2" component={Short2} fps={30} width={1080} height={1920}
        defaultProps={{ segs: AH2_SEGS, cover: "short2_cover.jpg", title: "ATOMIC HABITS", music: "short2_music.mp3" }}
        calculateMetadata={({ props }) => ({ durationInFrames: (props.segs as Seg[]).reduce((s, x) => s + Math.round(x.dur * 30), 0) })} />
      {/* Thumbnails for the ACTIVE book (Man's Search for Meaning). Backgrounds live in
          remotion/public/ — copy the chosen scene stills there before rendering.
          Keep each line under ~12 chars: 128px type overflows 1280 wide past that. */}
      {/* Must read COLD. "SUFFER CORRECTLY." on book #5 only parsed if you'd already
          watched the video — a payoff phrase, not a promise. Test each line against:
          would a stranger scrolling past understand what this video claims? */}
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "rmb_crash.png", line1: "Great rule.", line2: "False promise.", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "rmb_tenth.png", line1: "Keep the tenth.", line2: "Burn the rest.", side: "left" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "rmb_hook.png", line1: "Save for years.", line2: "Still broke?", side: "right" as const }} />
    </>
  );
};
