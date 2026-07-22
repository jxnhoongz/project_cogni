import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";
import { BookCover } from "./BookCover";
import { CREAM } from "./theme";

// The active book's acts, in order — these must match scenes.json `chapter` values,
// since finalize.py places Ch{n}.mov at each act's first beat (Ch1 skipped by default
// so the card doesn't cover the hook).
// PER-BOOK KNOBS — retarget BOTH of these together when the active book changes.
// The intro title used to be hardcoded inside Intro.tsx, which is how book #5 shipped
// a cut that opened with book #4's title card.
const BOOK_TITLE = "FREAKONOMICS";
const BOOK_AUTHOR = "Steven D. Levitt & Stephen J. Dubner";

const CHAPTERS = [
  "The Rogue and the Fine",
  "The Ones Grading the Test",
  "The Only One Who Knows",
  "The Crime That Vanished",
  "Your Own House",
  "What the Book Couldn't See",
  "The Verdict",
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Intro" component={Intro} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{ bookTitle: BOOK_TITLE }} />
      <Composition id="Outro" component={Outro} durationInFrames={210} fps={30} width={1920} height={1080} />
      <Composition id="BookCover" component={BookCover} durationInFrames={120} fps={30} width={1920} height={1080}
        defaultProps={{ cover: "book_cover.jpg", title: BOOK_TITLE, author: BOOK_AUTHOR }} />
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
        // Lands on beat 67 — the swimming pool is ~100x likelier than the gun to kill your
        // child. Clean round number, visceral, straight from the book's risk chapter.
        // ink=CREAM reads on most beats; the placement scene is a suburban exterior.
        defaultProps={{ value: 100, prefix: "", suffix: "×", kicker: "The pool, not the gun", sub: "100x likelier to kill", ink: CREAM }}
      />
      <Composition id="JuiceDemo" component={JuiceDemo} durationInFrames={750} fps={30} width={1920} height={1080} />
      {/* Thumbnails for the ACTIVE book (Man's Search for Meaning). Backgrounds live in
          remotion/public/ — copy the chosen scene stills there before rendering.
          Keep each line under ~12 chars: 128px type overflows 1280 wide past that. */}
      {/* Must read COLD. "SUFFER CORRECTLY." on book #5 only parsed if you'd already
          watched the video — a payoff phrase, not a promise. Test each line against:
          would a stranger scrolling past understand what this video claims? */}
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "v2_gate.png", line1: "Great book.", line2: "Bad science.", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "v2_coats.png", line1: "He was right.", line2: "Just not why.", side: "right" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "v2_sunday.png", line1: "Why Sunday", line2: "feels empty.", side: "right" as const }} />
    </>
  );
};
