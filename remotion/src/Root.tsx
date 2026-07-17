import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";

const CHAPTERS = [
  "The Gut Call",
  "Two Brains in One Skull",
  "The Candidate Who Reminded Him of Himself",
  "The Alarm System and the Broken Smoke Detector",
  "Selling the Winner, Holding the Loser",
  "The Boss, the Checklist, and the Slump That Wasn't a Slump",
  "The Verdict",
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
        defaultProps={{ value: 2, prefix: "", suffix: "×", kicker: "Losses hurt", sub: "as much as gains feel good" }}
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
