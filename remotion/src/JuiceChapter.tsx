import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily } from "./theme";

// A transparent chapter-marker overlay (upper-left), composited over the base at
// each chapter's first beat. ~4s (120 frames): slides in, holds, fades.
export const JuiceChapter: React.FC<{ index: number; title: string }> = ({ index, title }) => {
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

  const inX = interpolate(f, [0, 18], [-50, 0], ease);
  const op = interpolate(f, [0, 14, 96, 116], [0, 1, 1, 0], clamp);
  const rule = interpolate(f, [16, 40], [0, 320], ease);

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 110, top: 130, opacity: op, transform: `translateX(${inX}px)` }}>
        <div style={{ backgroundColor: "rgba(20,51,46,0.88)", padding: "26px 42px 30px", borderLeft: `8px solid ${OCHRE}`, maxWidth: 860 }}>
          <div style={{ fontFamily, color: OCHRE, fontSize: 26, letterSpacing: 9, textTransform: "uppercase" }}>
            Chapter {index}
          </div>
          <div style={{ width: rule, height: 3, backgroundColor: CREAM, opacity: 0.45, margin: "12px 0 14px" }} />
          <div style={{ fontFamily, color: CREAM, fontSize: 48, lineHeight: 1.02, textTransform: "uppercase" }}>
            {title}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
