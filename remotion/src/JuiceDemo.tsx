import React from "react";
import {
  AbsoluteFill,
  Easing,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/Anton";

const { fontFamily } = loadFont();

// --- Riso palette -----------------------------------------------------------
const CREAM = "#F1EDE4";
const TEAL = "#14332E";
const OCHRE = "#C6902F";

const TARGET = 40; // "...forty dollars more than he started with"

// Timing (frames @ 30fps, 750-frame / 25s comp). "forty dollars" lands ~5.7s.
const KICKER_IN = 100;
const REVEAL_START = 135; // number masks up into view
const REVEAL_END = 153;
const COUNT_START = 140;
const COUNT_END = 176; // settles ~5.9s
const RULE_START = 150;
const RULE_END = 172;
const FADE_OUT_START = 300;
const FADE_OUT_END = 338;

export const JuiceDemo: React.FC = () => {
  const frame = useCurrentFrame();

  const groupOpacity = interpolate(
    frame,
    [FADE_OUT_START, FADE_OUT_END],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const kickerOpacity = interpolate(frame, [KICKER_IN, KICKER_IN + 16], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const kickerY = interpolate(frame, [KICKER_IN, KICKER_IN + 16], [18, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Number rises up behind a masked baseline (no pop/bounce).
  const revealY = interpolate(frame, [REVEAL_START, REVEAL_END], [110, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const count = Math.round(
    interpolate(frame, [COUNT_START, COUNT_END], [0, TARGET], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    })
  );

  const ruleWidth = interpolate(frame, [RULE_START, RULE_END], [0, 470], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // The big number, drawn twice for a 2-ink Riso misregistration.
  const num = (color: string) => (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        display: "flex",
        alignItems: "flex-start",
        color,
        fontFamily,
        lineHeight: 1,
        whiteSpace: "nowrap",
      }}
    >
      <span style={{ fontSize: 150, marginTop: 34, marginRight: 6 }}>$</span>
      <span style={{ fontSize: 300 }}>{count}</span>
    </div>
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <OffthreadVideo
        src={staticFile("segment.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      {/* Editorial graphic in the left negative space — type on the art, no card */}
      <div style={{ position: "absolute", left: 130, top: 250, opacity: groupOpacity }}>
        {/* Kicker */}
        <div
          style={{
            fontFamily,
            color: OCHRE,
            fontSize: 34,
            letterSpacing: 9,
            textTransform: "uppercase",
            opacity: kickerOpacity,
            transform: `translateY(${kickerY}px)`,
            marginBottom: 14,
          }}
        >
          Not a paycheck
        </div>

        {/* Big count-up, masked reveal, ochre/teal misregistration */}
        <div style={{ overflow: "hidden", height: 320, width: 620 }}>
          <div
            style={{
              position: "relative",
              height: 320,
              transform: `translateY(${revealY}%)`,
            }}
          >
            <div style={{ position: "absolute", left: 7, top: 8 }}>{num(OCHRE)}</div>
            {num(TEAL)}
          </div>
        </div>

        {/* Hairline rule draws on */}
        <div
          style={{
            width: ruleWidth,
            height: 5,
            backgroundColor: TEAL,
            marginTop: 6,
          }}
        />
      </div>

      {/* Subtle print grain tying the type to the paper texture */}
      <AbsoluteFill
        style={{ opacity: 0.07, mixBlendMode: "multiply", pointerEvents: "none" }}
      >
        <svg width="100%" height="100%">
          <filter id="grain">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.9"
              numOctaves="2"
              stitchTiles="stitch"
            />
          </filter>
          <rect width="100%" height="100%" filter="url(#grain)" />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
