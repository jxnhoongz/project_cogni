import React from "react";
import { Composition } from "remotion";
import { JuiceDemo } from "./JuiceDemo";

// 25s @ 30fps = 750 frames. Matches remotion/public/segment.mp4.
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="JuiceDemo"
      component={JuiceDemo}
      durationInFrames={750}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
