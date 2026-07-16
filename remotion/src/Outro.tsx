import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily, Grain, Misreg } from "./theme";

// ~6s outro (180 frames @ 30fps): wordmark + sign-off + subscribe CTA.
export const Outro: React.FC = () => {
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

  const inOp = interpolate(f, [0, 15], [0, 1], clamp);
  const inY = interpolate(f, [0, 15], [28, 0], ease);
  const rule = interpolate(f, [18, 38], [0, 380], ease);
  const cta = interpolate(f, [46, 62], [0, 1], clamp);
  const ctaY = interpolate(f, [46, 62], [24, 0], ease);
  const out = interpolate(f, [156, 180], [1, 0], clamp);

  return (
    <AbsoluteFill style={{ backgroundColor: CREAM, justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity: out, textAlign: "center" }}>
        <div style={{ opacity: inOp, transform: `translateY(${inY}px)` }}>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <Misreg size={132}>COGNIBOT</Misreg>
          </div>
          <div style={{ width: rule, height: 4, backgroundColor: TEAL, margin: "16px auto" }} />
          <div style={{ fontFamily, color: TEAL, fontSize: 32, letterSpacing: 5, textTransform: "uppercase" }}>
            reads the next book so you don't have to
          </div>
        </div>

        {/* Subscribe CTA */}
        <div style={{ opacity: cta, transform: `translateY(${ctaY}px)`, marginTop: 46 }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 18,
            backgroundColor: TEAL, color: CREAM, fontFamily, fontSize: 40,
            letterSpacing: 6, textTransform: "uppercase", padding: "18px 48px",
          }}>
            <span style={{
              width: 0, height: 0,
              borderTop: "13px solid transparent", borderBottom: "13px solid transparent",
              borderLeft: `20px solid ${OCHRE}`,
            }} />
            Subscribe
          </div>
        </div>
      </div>
      <Grain />
    </AbsoluteFill>
  );
};
