import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily, Grain, Misreg } from "./theme";

// ~5s intro (150 frames @ 30fps): COGNIBOT + tagline, then the book title.
// The title is a PROP, not a literal: it used to be hardcoded here, so book #5 shipped
// with book #4's title card. It now lives beside CHAPTERS in Root.tsx — one place to
// retarget per book.
export const Intro: React.FC<{ bookTitle: string }> = ({ bookTitle }) => {
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

  const a1 = interpolate(f, [0, 15, 62, 78], [0, 1, 1, 0], clamp);
  const a1y = interpolate(f, [0, 15], [28, 0], ease);
  const rule1 = interpolate(f, [18, 40], [0, 380], ease);

  const a2 = interpolate(f, [80, 96, 134, 150], [0, 1, 1, 0], clamp);
  const a2y = interpolate(f, [80, 96], [28, 0], ease);

  return (
    <AbsoluteFill style={{ backgroundColor: CREAM, justifyContent: "center", alignItems: "center" }}>
      {/* Act 1 — the channel */}
      <div style={{ position: "absolute", opacity: a1, transform: `translateY(${a1y}px)`, textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Misreg size={156}>COGNIBOT</Misreg>
        </div>
        <div style={{ width: rule1, height: 4, backgroundColor: TEAL, margin: "18px auto" }} />
        <div style={{ fontFamily, color: OCHRE, fontSize: 30, letterSpacing: 7, textTransform: "uppercase" }}>
          my human lazy — me read book for human
        </div>
      </div>

      {/* Act 2 — the book */}
      <div style={{ position: "absolute", opacity: a2, transform: `translateY(${a2y}px)`, textAlign: "center" }}>
        <div style={{ fontFamily, color: OCHRE, fontSize: 28, letterSpacing: 12, textTransform: "uppercase", marginBottom: 18 }}>
          an honest verdict
        </div>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Misreg size={82}>{bookTitle}</Misreg>
        </div>
      </div>

      <Grain />
    </AbsoluteFill>
  );
};
