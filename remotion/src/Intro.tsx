import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { CREAM, OCHRE, TEAL, fontFamily, Grain, Misreg } from "./theme";

// ~6s intro (180 frames @ 30fps): COGNIBOT + tagline, then the book — real cover
// beside the title (this absorbed the old mid-video BookCover card; the intro already
// announces the book, so the cover lives here instead of interrupting a beat).
// Title/author/cover are PROPS, not literals: the title used to be hardcoded here, so
// book #5 shipped with book #4's title card. They live beside CHAPTERS in Root.tsx —
// one place to retarget per book. The cover is fetched legally
// (scripts/fetch_cover.py) into remotion/public/book_cover.jpg.
export const Intro: React.FC<{ bookTitle: string; author: string; cover?: string }> = ({
  bookTitle,
  author,
  cover = "book_cover.jpg",
}) => {
  const f = useCurrentFrame();
  const ease = { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
  const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

  const a1 = interpolate(f, [0, 15, 62, 78], [0, 1, 1, 0], clamp);
  const a1y = interpolate(f, [0, 15], [28, 0], ease);
  const rule1 = interpolate(f, [18, 40], [0, 380], ease);

  const a2 = interpolate(f, [80, 96, 164, 180], [0, 1, 1, 0], clamp);
  const coverY = interpolate(f, [80, 102], [70, 0], ease);
  const textX = interpolate(f, [90, 110], [40, 0], ease);
  const rule2 = interpolate(f, [104, 126], [0, 300], ease);

  // Misreg is nowrap — shrink long titles so they stay beside the cover
  // ("FREAKONOMICS" = 82; "MAN'S SEARCH FOR MEANING" would overflow at that size).
  const titleSize = bookTitle.length <= 14 ? 82 : bookTitle.length <= 22 ? 60 : 44;

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

      {/* Act 2 — the book: cover + verdict title, side by side */}
      <div style={{ position: "absolute", opacity: a2, display: "flex", alignItems: "center", gap: 64 }}>
        <div style={{ transform: `translateY(${coverY}px)`, boxShadow: "0 26px 60px rgba(20,51,46,0.35)" }}>
          <Img src={staticFile(cover)} style={{ height: 540, width: "auto", display: "block", borderRadius: 4 }} />
        </div>
        <div style={{ transform: `translateX(${textX}px)`, maxWidth: 860 }}>
          <div style={{ fontFamily, color: OCHRE, fontSize: 28, letterSpacing: 12, textTransform: "uppercase", marginBottom: 18 }}>
            an honest verdict
          </div>
          <Misreg size={titleSize}>{bookTitle}</Misreg>
          <div style={{ width: rule2, height: 5, backgroundColor: TEAL, margin: "26px 0 20px" }} />
          <div style={{ fontFamily, color: TEAL, fontSize: 32, letterSpacing: 3, opacity: 0.85 }}>
            {author}
          </div>
        </div>
      </div>

      <Grain />
    </AbsoluteFill>
  );
};
