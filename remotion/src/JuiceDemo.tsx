import React from "react";
import {
  AbsoluteFill,
  Easing,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// --- Riso palette -----------------------------------------------------------
const CREAM = "#F1EDE4";
const TEAL = "#14332E";
const OCHRE = "#C6902F";
const FONT =
  "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";

// Number spoken in this segment's narration ("...forty dollars more...").
const TARGET = 40;

// Timing (frames @ 30fps, 750-frame / 25s comp).
// The word "forty dollars" lands ~5.5s into the segment, so the count-up
// resolves right around there.
const KW_IN = 25; // keyword springs in ~0.8s
const KW_FADE_START = 122;
const KW_FADE_END = 148;

const CARD_IN = 150; // count-up card springs in as the keyword clears
const COUNT_START = 160; // ~5.3s
const COUNT_DUR = 36; // 1.2s ramp
const CARD_FADE_START = 340;
const CARD_FADE_END = 372;

export const JuiceDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // --- Kinetic keyword label: springs in, sits ~4s, fades out --------------
  const kwSpring = spring({
    frame: frame - KW_IN,
    fps,
    config: { damping: 12, mass: 0.6, stiffness: 120 },
  });
  const kwScale = interpolate(kwSpring, [0, 1], [0.8, 1]);
  const kwTranslateY = interpolate(kwSpring, [0, 1], [40, 0]);
  const kwOpacity = interpolate(
    frame,
    [KW_IN, KW_IN + 8, KW_FADE_START, KW_FADE_END],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // --- Count-up card --------------------------------------------------------
  const cardSpring = spring({
    frame: frame - CARD_IN,
    fps,
    config: { damping: 14, mass: 0.7, stiffness: 110 },
  });
  const cardScale = interpolate(cardSpring, [0, 1], [0.85, 1]);
  const cardTranslateY = interpolate(cardSpring, [0, 1], [34, 0]);
  const cardOpacity = interpolate(
    frame,
    [CARD_IN, CARD_IN + 8, CARD_FADE_START, CARD_FADE_END],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const rawCount = interpolate(
    frame,
    [COUNT_START, COUNT_START + COUNT_DUR],
    [0, TARGET],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );
  const count = Math.round(rawCount);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background: the real base video */}
      <OffthreadVideo
        src={staticFile("segment.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      {/* Kinetic keyword (upper-right third) */}
      <div
        style={{
          position: "absolute",
          top: 110,
          right: 130,
          opacity: kwOpacity,
          transform: `translateY(${kwTranslateY}px) scale(${kwScale})`,
          transformOrigin: "top right",
        }}
      >
        <div
          style={{
            display: "inline-block",
            backgroundColor: TEAL,
            color: CREAM,
            fontFamily: FONT,
            fontWeight: 800,
            fontSize: 46,
            letterSpacing: 4,
            textTransform: "uppercase",
            padding: "16px 30px",
            borderRadius: 12,
            borderBottom: `5px solid ${OCHRE}`,
            boxShadow: "0 14px 40px rgba(0,0,0,0.45)",
          }}
        >
          New Feeling
        </div>
      </div>

      {/* Count-up card (upper-right third, clear of bottom subtitles) */}
      <div
        style={{
          position: "absolute",
          top: 96,
          right: 130,
          opacity: cardOpacity,
          transform: `translateY(${cardTranslateY}px) scale(${cardScale})`,
          transformOrigin: "top right",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(20,51,46,0.82)",
            padding: "26px 42px 30px 42px",
            borderRadius: 20,
            borderLeft: `8px solid ${OCHRE}`,
            boxShadow: "0 20px 55px rgba(0,0,0,0.5)",
            textAlign: "right",
            backdropFilter: "blur(2px)",
          }}
        >
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: 5,
              textTransform: "uppercase",
              color: OCHRE,
              marginBottom: 4,
            }}
          >
            Made this weekend
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 900,
              fontSize: 150,
              lineHeight: 1,
              color: CREAM,
              letterSpacing: -2,
            }}
          >
            <span style={{ color: OCHRE, fontSize: 96, verticalAlign: "top" }}>
              $
            </span>
            {count}
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 600,
              fontSize: 24,
              color: CREAM,
              opacity: 0.85,
              marginTop: 2,
            }}
          >
            he didn&apos;t clock in for
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
