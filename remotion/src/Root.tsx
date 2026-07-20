import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";

// The active book's acts, in order — these must match scenes.json `chapter` values,
// since finalize.py places Ch{n}.mov at each act's first beat (Ch1 skipped by default
// so the card doesn't cover the hook).
const CHAPTERS = [
  "The Frozen Cursor",
  "The Book That Said You're Not Dumb",
  "Enough, and the Money You Can't See",
  "A Tail Worth Chasing",
  "Two Orders, No Rule",
  "The Boring Fund Catches Him",
  "Reasonable Is a Description, Not an Order",
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Intro" component={Intro} durationInFrames={150} fps={30} width={1920} height={1080} />
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
        // Lands on beat 68 — "Sixty thousand dollars. Gone." Numeric mode (not the word
        // reveal): 60 + "K" suffix rather than 60000, which would overflow the 620px mask.
        defaultProps={{ value: 60, prefix: "$", suffix: "K", kicker: "Comfort picked it", sub: "gone like a candle" }}
      />
      <Composition id="JuiceDemo" component={JuiceDemo} durationInFrames={750} fps={30} width={1920} height={1080} />
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "tf_book.png", line1: "Read the book.", line2: "Still biased.", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "tf_gut.png", line1: "Your gut lies.", line2: "Constantly.", side: "left" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "tf_brain.png", line1: "Know the bias.", line2: "Fall for it anyway.", side: "left" as const }} />
    </>
  );
};
