"""shortify — build a 9:16 Cognibot Short from a spec JSON.

A Short's editorial work (the hook, the beat-by-beat narration, which still goes with
which line, the crop bias, the captions, the pacing) is hand-authored in a spec file —
see shorts/atomic-habits-37x.json. This script does the MECHANICAL part around it:
narrate each line (edge-tts, the same plain-Brian voice as the videos), measure the
durations, stage the referenced stills + music into remotion/public, emit the render
spec, and render the Remotion `Short` composition to the book project's shorts/ folder.

Spec (shorts/<slug>.json):
  { slug, book: "<proj under projects/>", music: "<file in assets/audio>",
    narration: [ "<line per beat>", ... ],
    shots: [ {kind:"hook"|"end", dur, cap:[...]}       # brand cards, no still
             | {scene:<id>, pos:"x% y%", dur, cap:[...]} ] }   # a book still, crop-biased

The visual track (shots) and the narration track run in PARALLEL in the composition, so
sum(shot durs) should ~match sum(narration durs). shortify warns if they drift > 0.4s.

Usage:  python scripts/shortify.py shorts/atomic-habits-37x.json [--no-render]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC = REPO / "remotion" / "public"
VOICE = "en-US-BrianNeural"          # plain Brian — no multilingual accent-flip (see config.yaml)
FPS = 30


def _dur(mp3: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(mp3)], capture_output=True, text=True)
    return round(float(out.stdout.strip()), 2)


def build(spec_path: Path, do_render: bool) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    slug = spec["slug"]
    proj = REPO / "projects" / spec["book"]
    imgs = proj / "images"
    if not imgs.exists():
        raise SystemExit(f"no images dir at {imgs}")
    PUBLIC.mkdir(parents=True, exist_ok=True)

    # 1. narrate each beat -> public/<slug>_beat_N.mp3, measure duration
    narr = []
    for i, line in enumerate(spec["narration"], 1):
        mp3 = PUBLIC / f"{slug}_beat_{i}.mp3"
        subprocess.run([sys.executable, "-m", "edge_tts", "--voice", VOICE,
                        "--text", line, "--write-media", str(mp3)], check=True, capture_output=True)
        narr.append({"src": mp3.name, "dur": _dur(mp3)})
    print(f"[shortify] narrated {len(narr)} beats ({VOICE})")

    # 2. stage stills referenced by shots -> public/<slug>_sNNN.png; build shot props
    shots = []
    for s in spec["shots"]:
        if s.get("kind") in ("hook", "end"):
            shots.append({"kind": s["kind"], "dur": s["dur"], "cap": s["cap"]})
            continue
        src = imgs / f"scene_{int(s['scene']):03d}.png"
        if not src.exists():
            raise SystemExit(f"shot references missing still {src}")
        dst = PUBLIC / f"{slug}_s{int(s['scene']):03d}.png"
        dst.write_bytes(src.read_bytes())
        shots.append({"kind": "photo", "img": dst.name, "pos": s.get("pos", "50% 50%"),
                      "dur": s["dur"], "cap": s.get("cap")})

    # 3. stage music
    music = spec.get("music")
    if music:
        mdst = PUBLIC / f"{slug}_music.mp3"
        mdst.write_bytes((REPO / "assets" / "audio" / music).read_bytes())
        music = mdst.name

    # 4. sync check — the two tracks should sum to ~the same length
    a = sum(n["dur"] for n in narr)
    v = sum(s["dur"] for s in shots)
    flag = " <-- DRIFT >0.4s, retime shots" if abs(a - v) > 0.4 else ""
    print(f"[shortify] narration {a:.2f}s | visuals {v:.2f}s{flag}")

    # 5. write the render spec (props for the generic `Short` composition)
    render_spec = PUBLIC / f"{slug}.short.json"
    render_spec.write_text(json.dumps({"narr": narr, "shots": shots, "music": music},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
    out = proj / "shorts" / f"{slug}.mp4"
    out.parent.mkdir(exist_ok=True)
    print(f"[shortify] wrote {render_spec.relative_to(REPO)}")

    if not do_render:
        print(f"[shortify] preview: cd remotion && npx remotion render src/index.ts Short "
              f'"{out}" --props="{render_spec}"')
        return

    print("[shortify] rendering ...")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "Short", str(out),
                        f"--props={render_spec}"], cwd=REPO / "remotion", shell=(sys.platform == "win32"))
    if r.returncode != 0:
        raise SystemExit("remotion render failed")
    print(f"[shortify] wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--no-render", action="store_true", help="stage assets + write spec, skip the render")
    a = ap.parse_args()
    build(Path(a.spec), not a.no_render)


if __name__ == "__main__":
    main()
