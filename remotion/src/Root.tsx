import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";
import { CREAM } from "./theme";

// The active book's acts, in order — these must match scenes.json `chapter` values,
// since finalize.py places Ch{n}.mov at each act's first beat (Ch1 skipped by default
// so the card doesn't cover the hook).
// PER-BOOK KNOBS — retarget BOTH of these together when the active book changes.
// The intro title used to be hardcoded inside Intro.tsx, which is how book #5 shipped
// a cut that opened with book #4's title card.
const BOOK_TITLE = "EAT THAT FROG!";
const BOOK_AUTHOR = "Brian Tracy";

const CHAPTERS = [
  "The Frog on Your Desk",
  "Which One Is the Frog?",
  "Sorting the Swamp",
  "Down the Hatch",
  "The Last Frog Is You",
  "The Numbers Don't Survive",
  "The Verdict: Eat It Anyway",
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
        // Lands on beat 77 — the Lally (UCL) habit study: median 66 days to automaticity,
        // vs the 21-day rule Tracy repeats. OUR verified number, graded against the book's.
        // ink=CREAM default; re-check against the placement beat's background at verify.
        defaultProps={{ value: 66, prefix: "", suffix: "", kicker: "days to automatic", sub: "Tracy promised 21", ink: CREAM }}
      />
      <Composition id="JuiceDemo" component={JuiceDemo} durationInFrames={750} fps={30} width={1920} height={1080} />
      {/* Thumbnails for the ACTIVE book (Man's Search for Meaning). Backgrounds live in
          remotion/public/ — copy the chosen scene stills there before rendering.
          Keep each line under ~12 chars: 128px type overflows 1280 wide past that. */}
      {/* Must read COLD. "SUFFER CORRECTLY." on book #5 only parsed if you'd already
          watched the video — a payoff phrase, not a promise. Test each line against:
          would a stranger scrolling past understand what this video claims? */}
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "etf_frogplate.png", line1: "Great rule.", line2: "Fake stats.", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "etf_ghost.png", line1: "The study", line2: "never existed.", side: "left" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "etf_mirror.png", line1: "The frog", line2: "is you.", side: "right" as const }} />
    </>
  );
};
