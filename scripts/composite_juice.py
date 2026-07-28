"""Composite the Remotion juice overlays (chapter cards + count-up) onto an
assembled video at absolute timestamps derived from scenes.json durations.

Post-pass, decoupled from assemble.py: each overlay is a transparent 1920x1080
ProRes-4444 (yuva) clip, ~4s, placed at the START of its target scene. We shift
each overlay's PTS to its scene's cumulative start time and gate it with an
`enable` window, then re-encode the base once (nvenc) copying the audio.

Usage:
  python composite_juice.py [--in IN.mp4] [--out OUT.mp4] [--include-ch1]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PROJ = Path(r"D:\projects\project_cogni\projects\rich-dad-poor-dad")
SCENES = PROJ / "scenes.json"
JUICE = PROJ / "juice"
OVERLAY_SEC = 4.0  # each overlay comp is 120f @ 30fps

# scene_id -> overlay filename. Ch1 (scene 1, the hook) is opt-in: the card would
# cover Marcus and the intro already frames the book, so it's off by default.
JUICE_MAP_BASE = {
    14: "Ch2.mov",
    27: "Ch3.mov",
    40: "Ch4.mov",
    53: "Ch5.mov",
    66: "Ch6.mov",
    79: "Ch7.mov",
    67: "Countup67.mov",
}


def scene_starts() -> dict[int, float]:
    doc = json.loads(SCENES.read_text(encoding="utf-8"))
    t = 0.0
    starts: dict[int, float] = {}
    for s in doc["scenes"]:
        starts[s["id"]] = t
        t += s.get("duration_sec") or 0.0
    return starts


def build(src: Path, out: Path, include_ch1: bool) -> list[str]:
    starts = scene_starts()
    jmap = dict(JUICE_MAP_BASE)
    if include_ch1:
        jmap[1] = "Ch1.mov"

    # Order overlays by start time for a readable chain.
    items = sorted(jmap.items(), key=lambda kv: starts[kv[0]])

    inputs: list[str] = ["-i", str(src)]
    for _, mov in items:
        inputs += ["-i", str(JUICE / mov)]

    parts: list[str] = []
    for i, (sid, mov) in enumerate(items, start=1):
        t0 = starts[sid]
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS+{t0:.3f}/TB[o{i}]")

    cur = "0:v"
    for i, (sid, mov) in enumerate(items, start=1):
        t0 = starts[sid]
        nxt = f"v{i}"
        parts.append(
            f"[{cur}][o{i}]overlay=0:0:eof_action=pass:"
            f"enable='between(t,{t0:.3f},{t0 + OVERLAY_SEC:.3f})'[{nxt}]"
        )
        cur = nxt

    filtergraph = ";".join(parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filtergraph,
        "-map", f"[{cur}]", "-map", "0:a?",
        "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-b:v", "12M",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out),
    ]
    # Log the placement plan.
    for sid, mov in items:
        m = int(starts[sid] // 60); s = int(starts[sid] % 60)
        print(f"  {mov:<12} -> scene {sid:>2} @ {m}:{s:02d} ({starts[sid]:.1f}s)")
    return cmd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=str(PROJ / "output" / "final.mp4"))
    ap.add_argument("--out", dest="out", default=str(PROJ / "output" / "final_juiced.mp4"))
    ap.add_argument("--include-ch1", action="store_true")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    if not src.exists():
        raise SystemExit(f"input not found: {src}")
    cmd = build(src, out, a.include_ch1)
    print(f"\ncompositing {src.name} -> {out.name} ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("\n".join(r.stderr.strip().splitlines()[-15:]))
        raise SystemExit("ffmpeg failed")
    print(f"wrote {out} ({out.stat().st_size/1e6:.0f} MB)")


if __name__ == "__main__":
    main()
