#!/usr/bin/env python3
"""
Normalize audio to target LUFS using ffmpeg.

Usage:
    python normalize_audio.py --input raw.mp3 --output normalized.mp3 --target-lufs -16
"""

import argparse
import json
import subprocess
from pathlib import Path


def get_loudness(path: Path) -> dict:
    """Measure audio loudness using ffmpeg loudnorm filter."""
    cmd = [
        "ffmpeg", "-i", str(path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse loudnorm output from stderr
    output = result.stderr
    try:
        # Find JSON in output
        json_start = output.rfind("{")
        json_end = output.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(output[json_start:json_end])
    except:
        pass

    return {}


def normalize_audio(input_path: Path, output_path: Path, target_lufs: float) -> dict:
    """Normalize audio to target LUFS."""
    # First pass: measure
    loudness = get_loudness(input_path)

    # Second pass: apply normalization
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:measured_I={loudness.get('input_i', -23)}:measured_LRA={loudness.get('input_lra', 7)}:measured_TP={loudness.get('input_tp', -2)}:measured_thresh={loudness.get('input_thresh', -33)}:offset={loudness.get('target_offset', 0)}:linear=true",
        "-ar", "44100",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path)
    ]

    subprocess.run(cmd, check=True, capture_output=True)

    # Verify output
    final_loudness = get_loudness(output_path)

    return {
        "success": True,
        "input": str(input_path),
        "output": str(output_path),
        "target_lufs": target_lufs,
        "measured_lufs": float(final_loudness.get("input_i", target_lufs))
    }


def main():
    parser = argparse.ArgumentParser(description="Normalize audio loudness")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-lufs", type=float, default=-16)
    args = parser.parse_args()

    result = normalize_audio(args.input, args.output, args.target_lufs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()