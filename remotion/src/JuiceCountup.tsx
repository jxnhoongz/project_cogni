import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily } from "./theme";

// Transparent editorial count-up overlay (big number, ink misregistration, kicker,
// hairline rule) for the left negative space. ~4s (120 frames).
// `ink` is the top layer of the misregistration (number, rule, sub); OCHRE always sits
// behind it. TEAL reads on a light beat but disappears on a dark one — book #5's count-up
// lands on a dark teal wall, where the sub and rule vanished entirely. Pick it to contrast
// with the beat the count-up actually sits on.
export const JuiceCountup: React.FC<{ value?: number; kicker: string; sub: string; prefix?: string; suffix?: string; word?: string; ink?: string }> = ({ value = 0, kicker, sub, prefix = "$", suffix = "", word, ink = TEAL }) => {
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

  const group = interpolate(f, [0, 12, 96, 116], [0, 1, 1, 0], clamp);
  const kickerY = interpolate(f, [6, 22], [16, 0], ease);
  const revealY = interpolate(f, [18, 36], [110, 0], ease);
  const count = Math.round(interpolate(f, [22, 58], [0, value], { ...clamp, easing: Easing.out(Easing.cubic) }));
  const ruleW = interpolate(f, [34, 54], [0, 470], ease);

  // A book with no signature number (e.g. Psychology of Money) reveals a WORD instead of
  // counting — same masked reveal + ink misregistration, no numeric count.
  const wordSize = word ? Math.min(300, Math.floor(720 / Math.max(word.length, 1) * 1.6)) : 300;
  const num = (color: string) => (
    <div style={{ position: "absolute", top: 0, left: 0, display: "flex", alignItems: "flex-start", color, fontFamily, lineHeight: 1, whiteSpace: "nowrap" }}>
      {word ? (
        <span style={{ fontSize: wordSize, textTransform: "uppercase", letterSpacing: 2 }}>{word}</span>
      ) : (
        <>
          {prefix ? <span style={{ fontSize: 150, marginTop: 34, marginRight: 6 }}>{prefix}</span> : null}
          <span style={{ fontSize: 300 }}>{count}</span>
          {suffix ? <span style={{ fontSize: 150, marginTop: 34, marginLeft: 6 }}>{suffix}</span> : null}
        </>
      )}
    </div>
  );

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 130, top: 250, opacity: group }}>
        <div style={{ fontFamily, color: OCHRE, fontSize: 34, letterSpacing: 9, textTransform: "uppercase", transform: `translateY(${kickerY}px)`, marginBottom: 14 }}>
          {kicker}
        </div>
        <div style={{ overflow: "hidden", height: 320, width: 620 }}>
          <div style={{ position: "relative", height: 320, transform: `translateY(${revealY}%)` }}>
            <div style={{ position: "absolute", left: 7, top: 8 }}>{num(OCHRE)}</div>
            {num(ink)}
          </div>
        </div>
        <div style={{ width: ruleW, height: 5, backgroundColor: ink, marginTop: 6 }} />
        <div style={{ fontFamily, color: ink, fontSize: 30, letterSpacing: 4, textTransform: "uppercase", marginTop: 14, opacity: 0.85 }}>
          {sub}
        </div>
      </div>
    </AbsoluteFill>
  );
};
