"""Transcribe a reference video (Douyin/YouTube/local file) to a timestamped script.

For STUDYING STRUCTURE — how a channel we admire paces a book breakdown — not for
copying its words. Output lands in `research/transcripts/` which is gitignored: another
creator's script doesn't belong in our repo.

    python scripts/transcribe.py <file|url> [--lang zh] [--model large-v3] [--translate]

Runs faster-whisper locally (CTranslate2, no PyTorch). Free, no API, no credits.
GPU if CUDA is available, else CPU int8 — a 3-minute clip is quick either way.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "research" / "transcripts"


def fetch(src: str, work: Path) -> Path:
    """A URL goes through yt-dlp; a local path is used as-is."""
    if not src.startswith(("http://", "https://")):
        p = Path(src)
        if not p.exists():
            raise SystemExit(f"no such file: {p}")
        return p
    work.mkdir(parents=True, exist_ok=True)
    out = work / "source.%(ext)s"
    print(f"[fetch] yt-dlp {src}")
    subprocess.run(["yt-dlp", "-o", str(out), src], check=True)
    got = sorted(work.glob("source.*"))
    if not got:
        raise SystemExit("yt-dlp produced no file")
    return got[0]


def to_wav(src: Path, wav: Path) -> Path:
    """16 kHz mono — what Whisper wants; avoids it resampling internally."""
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-ac", "1", "-ar", "16000", "-vn", str(wav)],
        check=True,
    )
    return wav


def pick_device() -> tuple[str, str]:
    """GPU when CUDA is usable, else CPU. int8 keeps both fast and small."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def hms(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="local video/audio file, or a URL for yt-dlp")
    ap.add_argument("--lang", default="zh", help="spoken language (zh, en, ...)")
    ap.add_argument("--model", default="large-v3", help="whisper model size")
    ap.add_argument("--translate", action="store_true",
                    help="also write an English translation alongside the original")
    ap.add_argument("--name", default=None, help="output basename (default: source stem)")
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    work = OUT_DIR / "_work"
    src = fetch(args.source, work)
    stem = args.name or src.stem
    wav = to_wav(src, work / f"{stem}.wav")

    device, compute = pick_device()
    print(f"[whisper] model={args.model} device={device} ({compute}) lang={args.lang}")
    model = WhisperModel(args.model, device=device, compute_type=compute)

    def run(task: str) -> list:
        segs, info = model.transcribe(
            str(wav), language=args.lang, task=task,
            vad_filter=True,                      # drop silence so timings mean something
            vad_parameters={"min_silence_duration_ms": 400},
        )
        segs = list(segs)
        return segs, info

    segments, info = run("transcribe")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    txt = OUT_DIR / f"{stem}.txt"
    with txt.open("w", encoding="utf-8") as f:
        f.write(f"# {stem} — {args.lang}, {info.duration:.0f}s\n\n")
        for s in segments:
            f.write(f"[{hms(s.start)}] {s.text.strip()}\n")
    print(f"[whisper] wrote {txt}")

    if args.translate:
        en, _ = run("translate")
        etxt = OUT_DIR / f"{stem}.en.txt"
        with etxt.open("w", encoding="utf-8") as f:
            f.write(f"# {stem} — English translation, {info.duration:.0f}s\n\n")
            for s in en:
                f.write(f"[{hms(s.start)}] {s.text.strip()}\n")
        print(f"[whisper] wrote {etxt}")

    # Structural read — the numbers we compare against our own scripts.
    dur = info.duration
    chars = sum(len(s.text.strip()) for s in segments)
    gaps = [b.start - a.end for a, b in zip(segments, segments[1:])]
    print(f"\n[structure] {hms(dur)} total, {len(segments)} segments")
    print(f"[structure] {chars} chars, {chars / (dur / 60):.0f} chars/min "
          f"(density: how much is actually said per minute)")
    print(f"[structure] segment every {dur / max(len(segments), 1):.1f}s on average")
    if gaps:
        print(f"[structure] longest pause {max(gaps):.2f}s — beat breaks live here")
    print(f"\nFirst 30s (the hook):")
    for s in segments:
        if s.start > 30:
            break
        print(f"  [{hms(s.start)}] {s.text.strip()}")


if __name__ == "__main__":
    sys.exit(main())
