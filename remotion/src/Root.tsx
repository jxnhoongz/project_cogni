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
const BOOK_TITLE = "MAN'S SEARCH FOR MEANING";

const CHAPTERS = [
  "The Sunday Feeling",
  "The Man Who Refused the Visa",
  "Two Races of Men",
  "The Will to Meaning",
  "The Doctor Who Sits Up",
  "What the Dead Can't Tell You",
  "The Coat on the Pile",
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Intro" component={Intro} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{ bookTitle: BOOK_TITLE }} />
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
        // Lands on beat 13 — he dictated the book in nine straight days. A count-up puts a
        // number on screen as flat fact, so it must be one the BOOK supports: this one was
        // checked against the text ("within nine successive days"). Don't graphic a figure
        // the model recalled from training — that is how "sixteen million copies" got in.
        // ink=CREAM: beat 13 is a dim Vienna interior; the default TEAL would vanish.
        defaultProps={{ value: 9, prefix: "", suffix: "", kicker: "He dictated it in", sub: "nine straight days", ink: CREAM }}
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
