import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, Easing, interpolate, staticFile, useCurrentFrame } from "remotion";
import { CREAM, TEAL, OCHRE, fontFamily, Grain, Misreg } from "./theme";

// A 9:16 Short from a book's existing stills + fresh narration, DUAL-TRACK: narration
// runs continuous on one track while the visual track cuts every ~2-4s (the pilot's
// v0 held one still for 10-12s and dragged — Shorts need a refresh every few seconds).
// Stills are cropped toward the subject via CSS object-position (blur-pad looks weak on
// our wide art). Frame 1 is a puzzle HOOK card; last shot is the CTA. No channel bumper.

export type Narr = { src: string; dur: number };                       // one narration beat
export type Shot = { kind: "hook" | "photo" | "end"; img?: string; pos?: string; dur: number; cap?: string[] };

const FPS = 30;
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
const easeOut = { easing: Easing.out(Easing.cubic), ...clamp };

const Caption: React.FC<{ lines: string[] }> = ({ lines }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [1, 7], [0, 1], clamp);
  const y = interpolate(f, [1, 7], [22, 0], easeOut);
  return (
    <div style={{
      position: "absolute", left: 0, right: 0, bottom: 250, textAlign: "center",
      opacity: op, transform: `translateY(${y}px)`, padding: "0 55px",
    }}>
      {lines.map((l, i) => (
        <div key={i} style={{
          fontFamily, fontSize: lines.length === 1 ? 128 : 108, lineHeight: 1.02,
          color: i === lines.length - 1 ? OCHRE : CREAM, textTransform: "uppercase",
          textShadow: "0 6px 26px rgba(0,0,0,0.72)", WebkitTextStroke: "2px rgba(10,25,22,0.55)",
        }}>{l}</div>
      ))}
    </div>
  );
};

const PhotoShot: React.FC<{ img: string; pos: string; lines?: string[]; frames: number }> = ({ img, pos, lines, frames }) => {
  const f = useCurrentFrame();
  const scale = interpolate(f, [0, frames], [1.04, 1.12], clamp);     // push-in over the shot
  const inOp = interpolate(f, [0, 4], [0, 1], clamp);                 // tiny fade so hard cuts don't flash
  return (
    <AbsoluteFill style={{ backgroundColor: TEAL, overflow: "hidden", opacity: inOp }}>
      <Img src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: pos, transform: `scale(${scale})` }} />
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, transparent 50%, rgba(10,25,22,0.74) 88%)" }} />
      {lines && <Caption lines={lines} />}
    </AbsoluteFill>
  );
};

const HookCard: React.FC<{ lines: string[] }> = ({ lines }) => {
  const f = useCurrentFrame();
  const a = interpolate(f, [0, 8], [0, 1], clamp);
  const y = interpolate(f, [0, 10], [26, 0], easeOut);
  const rule = interpolate(f, [8, 24], [0, 420], easeOut);
  const l2 = interpolate(f, [12, 24], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ backgroundColor: CREAM, justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity: a, transform: `translateY(${y}px)`, textAlign: "center" }}>
        <div style={{ fontFamily, color: OCHRE, fontSize: 40, letterSpacing: 10, textTransform: "uppercase", marginBottom: 38 }}>
          The math they sold you
        </div>
        <div style={{ display: "flex", justifyContent: "center" }}><Misreg size={160}>{lines[0]}</Misreg></div>
        <div style={{ width: rule, height: 6, backgroundColor: TEAL, margin: "38px auto" }} />
        <div style={{ display: "flex", justifyContent: "center", opacity: l2 }}><Misreg size={160}>{lines[1]}</Misreg></div>
      </div>
      <Grain />
    </AbsoluteFill>
  );
};

const EndCard: React.FC<{ lines: string[] }> = ({ lines }) => {
  const f = useCurrentFrame();
  const a = interpolate(f, [0, 10], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ backgroundColor: CREAM, justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity: a, textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center" }}><Misreg size={130}>COGNIBOT</Misreg></div>
        <div style={{ width: 360, height: 5, backgroundColor: TEAL, margin: "26px auto" }} />
        <div style={{ fontFamily, color: TEAL, fontSize: 46, lineHeight: 1.06, textTransform: "uppercase" }}>
          {lines[0]}<br />{lines[1]}
        </div>
        <div style={{ marginTop: 50, display: "inline-block", backgroundColor: TEAL, color: CREAM, fontFamily, fontSize: 44, letterSpacing: 4, padding: "22px 54px", textTransform: "uppercase" }}>
          ▶ Subscribe
        </div>
      </div>
      <Grain />
    </AbsoluteFill>
  );
};

export const Short: React.FC<{ narr: Narr[]; shots: Shot[]; music?: string }> = ({ narr, shots, music }) => {
  let a = 0, v = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: TEAL }}>
      {music && <Audio src={staticFile(music)} volume={0.1} loop />}
      {/* narration track — continuous */}
      {narr.map((n, i) => {
        const len = Math.round(n.dur * FPS); const from = a; a += len;
        return <Sequence key={`a${i}`} from={from} durationInFrames={len}><Audio src={staticFile(n.src)} /></Sequence>;
      })}
      {/* visual track — fast cuts, independent of narration boundaries */}
      {shots.map((s, i) => {
        const len = Math.round(s.dur * FPS); const from = v; v += len;
        return (
          <Sequence key={`v${i}`} from={from} durationInFrames={len}>
            {s.kind === "hook" ? <HookCard lines={s.cap!} />
              : s.kind === "end" ? <EndCard lines={s.cap!} />
              : <PhotoShot img={s.img!} pos={s.pos ?? "50% 50%"} lines={s.cap} frames={len} />}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
