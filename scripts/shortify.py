"""shortify — build a 9:16 karaoke Short from a spec JSON.

The editorial work (the hook, the beat-by-beat narration, which still backs each line) is
hand-authored in a spec. This script does the mechanical rest: narrate each segment
(plain-Brian edge-tts), get REAL per-word timings from faster-whisper, group the words
into short lines and auto-pick each line's keyword, stage the stills + cover + music, and
render the Remotion `Short2` composition (persistent top-left book badge; centre-safe
karaoke captions where the keyword sits in ochre and the spoken word scales in sync).

Spec (shorts/<slug>.json):
  { slug, book: "<proj under projects/>", title: "ATOMIC HABITS",
    cover: {title, author}   # fetched legally; OR cover_file: "<path>"
    music: "<file in assets/audio>",
    segments: [ {text: "<narration line>", scene: <img id or null>, pos?: "x% y%"}, ... ] }
The LAST segment with scene:null becomes a SILENT COGNIBOT sign-off (no VO — the short
ends on the last teaching line; direction B). Any `text` on that segment is ignored.

Usage:  python scripts/shortify.py shorts/<slug>.json [--no-render]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC = REPO / "remotion" / "public"
VOICE = "en-US-BrianNeural"
FPS = 30
END_CARD_SEC = 2.6   # silent COGNIBOT sign-off (direction B — no spoken outro)
STOP = {"THE", "A", "TO", "OF", "AND", "IS", "YOU", "IT'S", "SO", "BE", "IN", "FOR", "DON'T",
        "WHO", "NOT", "AN", "YOUR", "YOU'RE", "THIS", "THAT'S", "OUT", "ONE", "EVERY", "ON"}


def _dur(mp3: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(mp3)], capture_output=True, text=True)
    return round(float(r.stdout.strip()), 2)


def _lines(words: list[dict]) -> list[dict]:
    """Group timed words into <=4-word lines (break on punctuation); tag each line's keyword
    (longest non-stopword) so the caption can hold it in ochre."""
    clean = [{"w": w["w"].replace("/", "").strip(), "t": w["t"]} for w in words if w["w"].replace("/", "").strip()]
    lines, cur = [], []
    for w in clean:
        cur.append({"w": w["w"].rstrip(".,:;?!"), "t": w["t"]})
        if w["w"].rstrip()[-1:] in ".,:;?!" or len(cur) >= 4:
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    out = []
    for ln in lines:
        k, kl = len(ln) - 1, -1
        for i, w in enumerate(ln):
            if w["w"] not in STOP and len(w["w"]) > kl:
                kl, k = len(w["w"]), i
        out.append({"k": k, "ws": ln})
    return out


def build(spec_path: Path, do_render: bool) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    slug = spec["slug"]
    proj = REPO / "projects" / spec["book"]
    imgs = proj / "images"
    PUBLIC.mkdir(parents=True, exist_ok=True)

    from faster_whisper import WhisperModel
    print("[shortify] loading whisper (base.en) ...")
    whisper = WhisperModel("base.en", device="cpu", compute_type="int8")

    segs = []
    for i, s in enumerate(spec["segments"], 1):
        if s.get("scene") is None:
            # Direction B: a SILENT quiet end card — no VO, no karaoke sell. The short's last
            # heard line is the final teaching beat; a gentle COGNIBOT card fades in over music.
            segs.append({"dur": END_CARD_SEC, "img": None, "audio": None, "lines": []})
            print(f"[shortify] seg {i}: {END_CARD_SEC}s END CARD (silent)")
            continue
        mp3 = PUBLIC / f"{slug}_seg_{i}.mp3"
        subprocess.run([sys.executable, "-m", "edge_tts", "--voice", VOICE,
                        "--text", s["text"], "--write-media", str(mp3)], check=True, capture_output=True)
        wsegs, _ = whisper.transcribe(str(mp3), word_timestamps=True, language="en")
        words = [{"w": w.word.strip().upper(), "t": round(w.start, 2)} for ws in wsegs for w in (ws.words or [])]
        src = imgs / f"scene_{int(s['scene']):03d}.png"
        if not src.exists():
            raise SystemExit(f"segment {i} references missing still {src}")
        dst = PUBLIC / f"{slug}_s{int(s['scene']):03d}.png"
        dst.write_bytes(src.read_bytes())
        seg = {"dur": _dur(mp3), "audio": mp3.name, "lines": _lines(words),
               "img": dst.name, "pos": s.get("pos", "50% 46%")}
        segs.append(seg)
        print(f"[shortify] seg {i}: {seg['dur']}s, {len(seg['lines'])} lines, still {seg['img']}")

    # cover: fetch legally, or copy a provided file
    cov = PUBLIC / f"{slug}_cover.jpg"
    if spec.get("cover_file"):
        cov.write_bytes(Path(spec["cover_file"]).read_bytes())
    else:
        c = spec["cover"]
        subprocess.run([sys.executable, str(REPO / "scripts" / "fetch_cover.py"), c["title"],
                        "--author", c.get("author", ""), "--out", str(cov)], check=True, capture_output=True)

    (PUBLIC / f"{slug}_music.mp3").write_bytes((REPO / "assets" / "audio" / spec["music"]).read_bytes())

    props = {"segs": segs, "cover": cov.name, "title": spec["title"], "music": f"{slug}_music.mp3"}
    spec_out = PUBLIC / f"{slug}.short.json"
    spec_out.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    total = round(sum(s["dur"] for s in segs), 1)
    out = proj / "shorts" / f"{slug}.mp4"
    out.parent.mkdir(exist_ok=True)
    print(f"[shortify] {total}s, wrote {spec_out.relative_to(REPO)}")

    if not do_render:
        print(f'[shortify] render: cd remotion && npx remotion render src/index.ts Short2 "{out}" --props="{spec_out}"')
        return
    print("[shortify] rendering Short2 ...")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "Short2", str(out), f"--props={spec_out}"],
                       cwd=REPO / "remotion", shell=(sys.platform == "win32"))
    if r.returncode != 0:
        raise SystemExit("remotion render failed")
    print(f"[shortify] wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    build(Path(a.spec), not a.no_render)


if __name__ == "__main__":
    main()
