#!/usr/bin/env python3
"""
Generate captions from audio using Whisper or AssemblyAI.

Usage:
    python generate_captions.py --audio vo.mp3 --output captions.ass [--format ass|srt]
"""

import argparse
import json
import subprocess
from pathlib import Path


def transcribe_whisper(audio_path: Path) -> list:
    """Transcribe using OpenAI Whisper (local)."""
    try:
        import whisper
    except ImportError:
        raise ImportError("whisper not installed: pip install openai-whisper")

    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path), word_timestamps=True)

    segments = []
    for segment in result.get("segments", []):
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })
    return segments


def format_timestamp_ass(seconds: float) -> str:
    """Format timestamp for ASS format (H:MM:SS.cc)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def format_timestamp_srt(seconds: float) -> str:
    """Format timestamp for SRT format (HH:MM:SS,mmm)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_ass(segments: list, output_path: Path):
    """Generate ASS subtitle file with styling."""
    header = """[Script Info]
Title: Generated Captions
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,50,50,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]
    for seg in segments:
        start = format_timestamp_ass(seg["start"])
        end = format_timestamp_ass(seg["end"])
        text = seg["text"].replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    output_path.write_text("\n".join(lines))


def generate_srt(segments: list, output_path: Path):
    """Generate SRT subtitle file."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp_srt(seg["start"])
        end = format_timestamp_srt(seg["end"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"])
        lines.append("")

    output_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Generate captions from audio")
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", default="ass", choices=["ass", "srt"])
    args = parser.parse_args()

    # Transcribe
    segments = transcribe_whisper(args.audio)

    # Generate output
    if args.format == "ass":
        generate_ass(segments, args.output)
    else:
        generate_srt(segments, args.output)

    print(json.dumps({
        "success": True,
        "output": str(args.output),
        "format": args.format,
        "segments": len(segments)
    }, indent=2))


if __name__ == "__main__":
    main()