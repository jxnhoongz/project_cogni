import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import { JuiceChapter } from "./JuiceChapter";
import { JuiceCountup } from "./JuiceCountup";
import { Thumbnail } from "./Thumbnail";

const CHAPTERS = [
  "The 6:47 AM Alarm That Always Loses",
  "1% Isn't Nothing — It's Everything (Eventually)",
  "Stop Chasing Goals, Start Being Someone",
  "The Four-Part Machine Behind Every Habit",
  "Move the Couch, Move the Habit",
  "Two Minutes, Habit Stacking, and the Trap of Instant Reward",
  "Six Months Later: What Actually Stuck",
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
        defaultProps={{ value: 37, prefix: "", suffix: "×", kicker: "1% better, every day", sub: "compounded over one year" }}
      />
      <Composition id="JuiceDemo" component={JuiceDemo} durationInFrames={750} fps={30} width={1920} height={1080} />
      <Composition id="ThumbA" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "ah_couch.png", line1: "Tiny habits.", line2: "Big promises?", side: "left" as const }} />
      <Composition id="ThumbB" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "ah_bed.png", line1: "1% better?", line2: "Or just hype?", side: "right" as const }} />
      <Composition id="ThumbC" component={Thumbnail} durationInFrames={1} fps={30} width={1280} height={720}
        defaultProps={{ bg: "ah_phone.png", line1: "Read it all.", line2: "Still lazy.", side: "left" as const }} />
    </>
  );
};
