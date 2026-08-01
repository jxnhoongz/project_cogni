import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, Easing, interpolate, staticFile, useCurrentFrame } from "remotion";
import { CREAM, TEAL, OCHRE, fontFamily, Grain, Misreg } from "./theme";

// Short v2 — teach-not-dunk, with the three things v1 lacked:
//  (1) a PERSISTENT top-left book badge (cover + title) — the one corner app UI leaves alone;
//  (2) KINETIC captions in the CENTRE safe zone (one phrase at a time, pop-synced to the
//      narration) — v1's captions sat low where Shorts UI covers them and only soft-faded;
//  (3) rhythmic push-in + a punch on every caption change, so stills feel driven.

export type Word = { t: number; w: string };
export type Line = { k: number; ws: Word[] };            // k = index of the keyword (ochre)
// img/audio are full staticFile names (scripts/shortify.py stages them); img null = end card.
// audio null = no VO for that segment (the end card is silent — see EndSeg / direction B).
export type Seg = { dur: number; img: string | null; audio: string | null; pos?: string; lines: Line[] };

const FPS = 30;
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
const easeOut = { easing: Easing.out(Easing.cubic), ...clamp };

// KARAOKE captions, dead-centre (clear of the top badge and the bottom ~30% app UI).
// The line stays put and fades in gently (no jarring per-phrase pop); its KEYWORD sits
// in ochre; the currently-spoken word scales up in exact sync (whisper word timings).
const KaraokeCaption: React.FC<{ lines: Line[] }> = ({ lines }) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  let li = 0;
  for (let i = 0; i < lines.length; i++) if (lines[i].ws[0].t <= t) li = i;   // active line
  const line = lines[li];
  const since = f - line.ws[0].t * FPS;                                       // frames since line began
  const op = interpolate(since, [0, 5], [0, 1], clamp);
  const rise = interpolate(since, [0, 6], [16, 0], easeOut);
  let wi = 0;
  for (let i = 0; i < line.ws.length; i++) if (line.ws[i].t <= t) wi = i;     // active word
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{
        display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 26px",
        maxWidth: 920, padding: "0 40px", opacity: op, transform: `translateY(${rise}px)`,
      }}>
        {line.ws.map((w, i) => {
          const active = i === wi;
          const key = i === line.k;
          const sc = interpolate(f - w.t * FPS, [0, 3, 7], [1, 1.14, active ? 1.1 : 1], easeOut);
          return (
            <span key={i} style={{
              fontFamily, fontSize: 112, lineHeight: 1.08, textTransform: "uppercase",
              color: key ? OCHRE : CREAM, opacity: active || key ? 1 : 0.72,
              transform: `scale(${sc})`, display: "inline-block",
              textShadow: "0 8px 30px rgba(0,0,0,0.85)", WebkitTextStroke: "3px rgba(8,20,18,0.7)",
            }}>{w.w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Badge: React.FC<{ cover: string; title: string }> = ({ cover, title }) => (
  <div style={{
    position: "absolute", top: 46, left: 46, display: "flex", alignItems: "center", gap: 20,
    background: "rgba(10,25,22,0.62)", borderRadius: 18, padding: "16px 26px 16px 16px",
    backdropFilter: "blur(2px)",
  }}>
    <Img src={staticFile(cover)} style={{ height: 132, width: "auto", borderRadius: 6, display: "block", boxShadow: "0 6px 18px rgba(0,0,0,0.5)" }} />
    <div>
      <div style={{ fontFamily, color: OCHRE, fontSize: 22, letterSpacing: 4, textTransform: "uppercase" }}>Cognibot · Book notes</div>
      <div style={{ fontFamily, color: CREAM, fontSize: 46, lineHeight: 1.0, textTransform: "uppercase", marginTop: 4 }}>{title}</div>
    </div>
  </div>
);

const PhotoSeg: React.FC<{ img: string; pos: string; lines: Line[]; frames: number }> = ({ img, pos, lines, frames }) => {
  const f = useCurrentFrame();
  const base = interpolate(f, [0, frames], [1.06, 1.17], clamp);          // slow push-in
  const t = f / FPS;
  let last = 0; for (const l of lines) if (l.ws[0].t <= t) last = l.ws[0].t;          // punch on each caption change
  const since = f - last * FPS;
  const punch = 0.028 * Math.max(0, 1 - since / 5);
  return (
    <AbsoluteFill style={{ backgroundColor: TEAL, overflow: "hidden" }}>
      <Img src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: pos, transform: `scale(${base * (1 + punch)})` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(8,20,18,0.35) 0%, rgba(8,20,18,0.15) 45%, rgba(8,20,18,0.55) 100%)" }} />
      <KaraokeCaption lines={lines} />
    </AbsoluteFill>
  );
};

// Direction B: a QUIET sign-off. No spoken outro (the short's last heard line is the final
// teaching beat), no karaoke sell, no loud gold button — just a gentle COGNIBOT wordmark that
// fades up over the music bed, with an understated subscribe cue. The spell doesn't break.
const EndSeg: React.FC = () => {
  const f = useCurrentFrame();
  const op = interpolate(f, [4, 18], [0, 1], easeOut);
  return (
    <AbsoluteFill style={{ backgroundColor: TEAL, justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity: op, textAlign: "center" }}>
        <Misreg size={84} color={CREAM}>COGNIBOT</Misreg>
        <div style={{ fontFamily, color: CREAM, opacity: 0.5, fontSize: 30, letterSpacing: 6, textTransform: "uppercase", marginTop: 30 }}>▶ subscribe</div>
      </div>
    </AbsoluteFill>
  );
};

export const Short2: React.FC<{ segs: Seg[]; cover: string; title: string; music?: string }> = ({ segs, cover, title, music }) => {
  let off = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: TEAL }}>
      {music && <Audio src={staticFile(music)} volume={0.09} loop />}
      {segs.map((s, i) => {
        const len = Math.round(s.dur * FPS); const from = off; off += len;
        return (
          <Sequence key={i} from={from} durationInFrames={len}>
            {s.audio && <Audio src={staticFile(s.audio)} />}
            {s.img ? <PhotoSeg img={s.img} pos={s.pos ?? "50% 46%"} lines={s.lines} frames={len} /> : <EndSeg />}
          </Sequence>
        );
      })}
      <Badge cover={cover} title={title} />   {/* persistent, above everything */}
      <Grain />
    </AbsoluteFill>
  );
};
