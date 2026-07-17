"""Finalize a Cognibot cut in ONE nvenc pass:
  output/final.mp4 (main)  ->  overlay Remotion juice (chapter cards + optional
  count-up) at each beat's timestamp  ->  prepend Intro, append Outro  ->
  output/final_full.mp4  (the upload file).

Project-aware: reads the active project (.active_project) and auto-detects each
chapter's first scene from scenes.json, so a chapter card lands at every chapter
start (Ch1 skipped so it doesn't cover the hook). Per-book knobs are the two
constants below.

Overlays are transparent 1920x1080 ProRes-4444 (yuva) ~4s comps in
projects/<slug>/juice/, rendered from Remotion with:
  --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png

Usage:  python scripts/finalize.py [--include-ch1]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INTRO = REPO / "remotion" / "out" / "intro.mp4"
OUTRO = REPO / "remotion" / "out" / "outro.mp4"
OVERLAY_SEC = 4.0

# --- per-book knob: a count-up overlay at one scene (or None to skip) ----------
COUNTUP_SCENE = 52            # scene id to place Countup.mov on (None = no count-up)


def active_slug() -> str:
    return (REPO / ".active_project").read_text(encoding="utf-8").strip()


def scene_starts(scenes: list[dict]) -> dict[int, float]:
    t, starts = 0.0, {}
    for s in scenes:
        starts[s["id"]] = t
        t += s.get("duration_sec") or 0.0
    return starts


def chapter_first_scenes(scenes: list[dict]) -> list[int]:
    """First scene id of each distinct chapter, in order of appearance."""
    seen, order = set(), []
    for s in scenes:
        c = s.get("chapter")
        if c is not None and c not in seen:
            seen.add(c)
            order.append(s["id"])
    return order


def build_cmd(proj: Path, base: Path, out: Path, include_ch1: bool) -> list[str]:
    doc = json.loads((proj / "scenes.json").read_text(encoding="utf-8"))
    scenes = doc["scenes"]
    starts = scene_starts(scenes)
    juice = proj / "juice"

    # chapter cards: Ch{n}.mov at each chapter's first scene (skip Ch1 by default)
    jmap: dict[int, str] = {}
    for n, sid in enumerate(chapter_first_scenes(scenes), start=1):
        if n == 1 and not include_ch1:
            continue
        mov = juice / f"Ch{n}.mov"
        if mov.exists():
            jmap[sid] = mov.name
    # optional count-up
    if COUNTUP_SCENE is not None and (juice / "Countup.mov").exists():
        jmap[COUNTUP_SCENE] = "Countup.mov"

    items = sorted(jmap.items(), key=lambda kv: starts[kv[0]])
    if not items:
        raise SystemExit(f"no juice overlays found in {juice}")

    inputs = ["-i", str(base), "-i", str(INTRO), "-i", str(OUTRO)]
    for _, mov in items:
        inputs += ["-i", str(juice / mov)]

    parts = []
    for i, (sid, _) in enumerate(items):
        parts.append(f"[{3 + i}:v]setpts=PTS-STARTPTS+{starts[sid]:.3f}/TB[o{i}]")
    cur = "0:v"
    for i, (sid, _) in enumerate(items):
        t0 = starts[sid]
        parts.append(f"[{cur}][o{i}]overlay=0:0:eof_action=pass:"
                     f"enable='between(t,{t0:.3f},{t0 + OVERLAY_SEC:.3f})'[m{i}]")
        cur = f"m{i}"
    parts.append(f"[{cur}]scale=1920:1080,setsar=1,fps=30,format=yuv420p[mv]")
    parts.append("[1:v]scale=1920:1080,setsar=1,fps=30,format=yuv420p[iv]")
    parts.append("[2:v]scale=1920:1080,setsar=1,fps=30,format=yuv420p[ov]")
    parts.append("[0:a]aresample=44100,aformat=channel_layouts=stereo[ma]")
    parts.append("[1:a]aresample=44100,aformat=channel_layouts=stereo[ia]")
    parts.append("[2:a]aresample=44100,aformat=channel_layouts=stereo[oa]")
    parts.append("[iv][ia][mv][ma][ov][oa]concat=n=3:v=1:a=1[vout][aout]")

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(parts),
           "-map", "[vout]", "-map", "[aout]",
           "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-b:v", "12M",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out)]
    print("juice placement:")
    for sid, mov in items:
        m, s = int(starts[sid] // 60), int(starts[sid] % 60)
        print(f"  {mov:<12} scene {sid:>2} @ {m}:{s:02d}")
    return cmd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-ch1", action="store_true")
    a = ap.parse_args()
    proj = REPO / "projects" / active_slug()
    base = proj / "output" / "final.mp4"
    out = proj / "output" / "final_full.mp4"
    for p in (base, INTRO, OUTRO):
        if not p.exists():
            raise SystemExit(f"missing input: {p}")
    cmd = build_cmd(proj, base, out, a.include_ch1)
    print(f"\nfinalizing {active_slug()} -> {out.name} (one nvenc pass) ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("\n".join(r.stderr.strip().splitlines()[-18:]))
        raise SystemExit("ffmpeg failed")
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(out)], capture_output=True, text=True)
    print(f"wrote {out} ({out.stat().st_size/1e6:.0f} MB, {dur.stdout.strip()}s)")


if __name__ == "__main__":
    main()
