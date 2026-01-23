#!/usr/bin/env python3
"""
Call TTS API to convert script to audio.

Usage:
    python call_tts_api.py --script script.json --output vo.mp3 [--provider elevenlabs|edge]
    python call_tts_api.py --script midform.json --by-chapter --output-dir ./chapters/

Requires:
    - ELEVENLABS_API_KEY environment variable for ElevenLabs
    - edge-tts package for Edge-TTS (pip install edge-tts)
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

VOICE_SETTINGS = {
    "elevenlabs": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - calm male
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.3,
        "use_speaker_boost": True
    },
    "edge": {
        "voice": "en-US-GuyNeural",
        "rate": "-5%",
        "pitch": "-2st"
    }
}


def call_elevenlabs(text: str, output_path: Path) -> dict:
    """Call ElevenLabs API."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")

    try:
        import requests
    except ImportError:
        raise ImportError("requests package required: pip install requests")

    settings = VOICE_SETTINGS["elevenlabs"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings['voice_id']}"

    response = requests.post(
        url,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": settings["stability"],
                "similarity_boost": settings["similarity_boost"],
                "style": settings["style"],
                "use_speaker_boost": settings["use_speaker_boost"]
            }
        }
    )

    if response.status_code == 200:
        output_path.write_bytes(response.content)
        return {"success": True, "provider": "elevenlabs", "file": str(output_path)}
    else:
        return {"success": False, "error": response.text}


def call_edge_tts(text: str, output_path: Path) -> dict:
    """Call Edge-TTS (free, local)."""
    settings = VOICE_SETTINGS["edge"]

    cmd = [
        "edge-tts",
        "--voice", settings["voice"],
        "--rate", settings["rate"],
        "--pitch", settings["pitch"],
        "--text", text,
        "--write-media", str(output_path)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return {"success": True, "provider": "edge", "file": str(output_path)}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.decode()}
    except FileNotFoundError:
        return {"success": False, "error": "edge-tts not installed: pip install edge-tts"}


def process_script(script_data: dict, provider: str, output_path: Path) -> dict:
    """Process script and generate audio."""
    # Extract text from script
    if "script" in script_data:
        text = script_data["script"]
    elif "chapters" in script_data:
        text = "\n\n".join(ch.get("script", "") for ch in script_data["chapters"])
    else:
        text = str(script_data)

    # Call appropriate provider
    if provider == "elevenlabs":
        result = call_elevenlabs(text, output_path)
    else:
        result = call_edge_tts(text, output_path)

    if result["success"]:
        # Get duration (requires ffprobe)
        try:
            duration = get_audio_duration(output_path)
            result["duration_sec"] = duration
        except:
            result["duration_sec"] = len(text.split()) / 2.5  # Estimate

    return result


def get_audio_duration(path: Path) -> float:
    """Get audio duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--by-chapter", action="store_true")
    parser.add_argument("--provider", default="edge", choices=["elevenlabs", "edge"])
    args = parser.parse_args()

    with open(args.script) as f:
        script_data = json.load(f)

    if args.by_chapter and "chapters" in script_data:
        # Process each chapter separately
        args.output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for i, chapter in enumerate(script_data["chapters"]):
            output_path = args.output_dir / f"chapter_{i:02d}.mp3"
            result = process_script({"script": chapter.get("script", "")}, args.provider, output_path)
            results.append(result)
        print(json.dumps({"chapters": results}, indent=2))
    else:
        # Process as single file
        result = process_script(script_data, args.provider, args.output)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()