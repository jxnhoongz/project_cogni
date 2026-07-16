import React from "react";
import { AbsoluteFill } from "remotion";
import { loadFont } from "@remotion/google-fonts/Anton";

export const { fontFamily } = loadFont();
export const CREAM = "#F1EDE4";
export const TEAL = "#14332E";
export const OCHRE = "#C6902F";

// Subtle print grain tying type to the paper texture.
export const Grain: React.FC = () => (
  <AbsoluteFill style={{ opacity: 0.06, mixBlendMode: "multiply", pointerEvents: "none" }}>
    <svg width="100%" height="100%">
      <filter id="grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
  </AbsoluteFill>
);

// 2-ink Riso misregistration: ochre copy offset behind a teal copy.
export const Misreg: React.FC<{ children: React.ReactNode; size: number; color?: string }> = ({
  children,
  size,
  color = TEAL,
}) => (
  <div style={{ position: "relative", fontFamily, fontSize: size, lineHeight: 1, whiteSpace: "nowrap" }}>
    <div style={{ position: "absolute", left: 5, top: 6, color: OCHRE }}>{children}</div>
    <div style={{ position: "relative", color }}>{children}</div>
  </div>
);
