import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily } from "./theme";

// A transparent "the book on the table today" card: the real cover slides up on the
// right with a title/byline beside it, holds, then fades. Composited over the book-intro
// beat so it's gone by the time the narration moves past the title. ~4.5s (135 frames).
// The cover is fetched legally (scripts/fetch_cover.py) into remotion/public/book_cover.jpg.
export const BookCover: React.FC<{ cover?: string; title: string; author: string }> = ({
  cover = "book_cover.jpg",
  title,
  author,
}) => {
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

  // fade fully out by frame 116 so it fits the 4.0s (120f) finalize overlay window
  const op = interpolate(f, [0, 16, 96, 116], [0, 1, 1, 0], clamp);
  const coverY = interpolate(f, [0, 22], [70, 0], ease);
  const textX = interpolate(f, [10, 30], [40, 0], ease);
  const rule = interpolate(f, [24, 46], [0, 300], ease);
  const kicker = interpolate(f, [4, 20], [12, 0], ease);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: op }}>
      <div style={{ display: "flex", alignItems: "center", gap: 56 }}>
        {/* the cover, with a drop shadow so it sits above the scene */}
        <div style={{ transform: `translateY(${coverY}px)`, boxShadow: "0 30px 80px rgba(0,0,0,0.55)" }}>
          <Img src={staticFile(cover)} style={{ height: 620, width: "auto", display: "block", borderRadius: 4 }} />
        </div>
        {/* title block */}
        <div style={{ transform: `translateX(${textX}px)`, maxWidth: 640 }}>
          <div style={{ fontFamily, color: OCHRE, fontSize: 30, letterSpacing: 10, textTransform: "uppercase", transform: `translateY(${kicker}px)`, marginBottom: 20 }}>
            Today's book
          </div>
          <div style={{ fontFamily, color: CREAM, fontSize: 88, lineHeight: 1.02, textTransform: "uppercase", textShadow: "0 6px 24px rgba(0,0,0,0.5)" }}>
            {title}
          </div>
          <div style={{ width: rule, height: 5, backgroundColor: OCHRE, margin: "26px 0 22px" }} />
          <div style={{ fontFamily, color: CREAM, fontSize: 34, letterSpacing: 3, opacity: 0.9 }}>
            {author}
          </div>
        </div>
      </div>
      {/* a soft scrim so cover + type read over any scene underneath */}
      <AbsoluteFill style={{ zIndex: -1, background: "radial-gradient(ellipse at center, rgba(20,51,46,0.72) 0%, rgba(20,51,46,0.42) 55%, rgba(20,51,46,0) 100%)" }} />
    </AbsoluteFill>
  );
};
