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
  "The Parking Lot",
  "The Comfortable Nothing",
  "My Cross to Carry",
  "The Trick That Actually Works",
  "Suffering Correctly",
  "Let the Record Play",
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Intro" component={Intro} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{ bookTitle: BOOK_TITLE }} />
      <Composition id="Outro" component={Outro} durationInFrames={180} fps={30} width={1920} height={1080} />
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
        // Lands on beat 72 — "Six months in and she's still reaching for the pen." The
        // motif is "six months", but "6 MONTHS" as prefix/suffix overflows the 620px
        // mask, so the numeral alone fills it and the kicker/sub carry the phrase:
        // "SHE SPENT / 6 / MONTHS MINING HER OWN PAIN".
        // ink=CREAM: beat 72 is a dark teal wall, where the default TEAL ink vanished.
        defaultProps={{ value: 6, prefix: "", suffix: "", kicker: "She spent", sub: "months mining her own pain", ink: CREAM }}
      />
      <Composition id="JuiceDemo" component={JuiceDemo} durationInFrames={750} fps={30} width={1920} height={1080} />
      {/* Thumbnails for the ACTIVE book (Man's Search for Meaning). Backgrounds live in
          remotion/public/ — copy the chosen scene stills there before rendering.
          Keep each line under ~12 chars: 128px type overflows 1280 wide past that. */}
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "msm_face.png", line1: "Suffer", line2: "correctly.", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "msm_car.png", line1: "She obeyed", line2: "the book.", side: "right" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "msm_floor.png", line1: "It came when", line2: "she quit.", side: "right" as const }} />
    </>
  );
};
