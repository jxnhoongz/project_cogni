import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily } from "./theme";

// YouTube thumbnail (1280x720). Low-poly still + bold editorial headline with a
// two-ink misregistration, and a scrim so the type stays legible over the art.
export const Thumbnail: React.FC<{
  bg: string;
  line1: string;
  line2: string;
  side: "left" | "right";
}> = ({ bg, line1, line2, side }) => {
  const alignRight = side === "right";
  const scrim = alignRight
    ? "linear-gradient(90deg, rgba(20,51,46,0) 30%, rgba(20,51,46,0.55) 62%, rgba(20,51,46,0.9) 100%)"
    : "linear-gradient(90deg, rgba(20,51,46,0.9) 0%, rgba(20,51,46,0.55) 38%, rgba(20,51,46,0) 70%)";

  // main ink + a single dark (teal) offset copy = a clean print "misprint" shadow
  // that stays legible over the art (no same-colour doubling).
  const Head = ({ text, color }: { text: string; color: string }) => (
    // The offset copy is positioned at left:7 of THIS box, so the box must hug its text
    // or the shadow strands itself on the far left of a right-aligned headline. The
    // parent is a flex column, which shrink-wraps each line to its content.
    <div style={{ position: "relative", lineHeight: 0.92, letterSpacing: 2, wordSpacing: 26 }}>
      <span style={{ position: "absolute", left: 7, top: 8, color: TEAL, opacity: 0.85 }}>{text}</span>
      <span style={{ position: "relative", color }}>{text}</span>
    </div>
  );

  return (
    <AbsoluteFill style={{ backgroundColor: TEAL }}>
      <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <AbsoluteFill style={{ background: scrim }} />
      <AbsoluteFill
        style={{
          padding: 70,
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          alignItems: alignRight ? "flex-end" : "flex-start",
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 128,
            textTransform: "uppercase",
            textAlign: alignRight ? "right" : "left",
            textShadow: "0 6px 24px rgba(0,0,0,0.45)",
            display: "flex",
            flexDirection: "column",
            alignItems: alignRight ? "flex-end" : "flex-start",
          }}
        >
          <Head text={line1} color={CREAM} />
          <Head text={line2} color={OCHRE} />
        </div>
      </AbsoluteFill>
      {/* small brand tag opposite the headline */}
      <div
        style={{
          position: "absolute",
          top: 40,
          [alignRight ? "left" : "right"]: 48,
          fontFamily,
          fontSize: 34,
          letterSpacing: 4,
          color: CREAM,
          opacity: 0.92,
          textShadow: "0 2px 10px rgba(0,0,0,0.5)",
        }}
      >
        COGNIBOT
      </div>
    </AbsoluteFill>
  );
};
