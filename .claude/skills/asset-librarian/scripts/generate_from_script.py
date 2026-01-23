#!/usr/bin/env python3
"""
Batch generate images for all scenes in a script.

Usage:
    python generate_from_script.py --script script.json --output-dir ./images/

Requires:
    - OPENAI_API_KEY environment variable
"""

import argparse
import json
import os
import requests
import base64
from datetime import datetime
from pathlib import Path

DAVINCI_STYLE = """Renaissance oil painting style, Leonardo da Vinci technique, \
sfumato shading, muted earth tones with ochre and umber, dramatic chiaroscuro lighting, \
museum quality fine art, 16th century Italian master painting, \
subtle atmospheric perspective, classical composition"""


def create_prompt(text: str) -> str:
    """Transform voiceover text into image generation prompt."""
    return f"Visual representation of: {text}\n\nStyle: {DAVINCI_STYLE}"


def generate_single_image(text: str, output_path: Path, landscape: bool = False) -> dict:
    """Generate single image using DALL-E 3 API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}

    prompt = create_prompt(text)
    size = "1792x1024" if landscape else "1024x1792"

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "standard",
            "response_format": "b64_json"
        }
    )

    if response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}

    data = response.json()
    image_data = data["data"][0]["b64_json"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(image_data))

    return {"success": True, "path": str(output_path)}


def generate_from_script(script_path: Path, output_dir: Path, landscape: bool = False) -> dict:
    """Generate images for all scenes in script."""
    with open(script_path) as f:
        script = json.load(f)

    # Extract segments/scenes from script
    segments = script.get("segments", script.get("scenes", []))
    if not segments:
        # Try to use the full script text split into chunks
        full_text = script.get("script", script.get("text", ""))
        if full_text:
            # Split by sentences or paragraphs
            segments = [{"text": full_text}]

    results = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, segment in enumerate(segments):
        text = segment.get("text", segment.get("voiceover", str(segment)))
        output_path = output_dir / f"scene_{i+1:02d}.png"

        print(f"Generating scene {i+1}/{len(segments)}...")
        result = generate_single_image(text, output_path, landscape)
        result["scene"] = i + 1
        result["input_text"] = text[:100] + "..." if len(text) > 100 else text
        results.append(result)

    return {
        "script": str(script_path),
        "total_scenes": len(segments),
        "generated": len([r for r in results if r.get("success")]),
        "output_dir": str(output_dir),
        "results": results,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }


def main():
    parser = argparse.ArgumentParser(description="Generate images for all script scenes")
    parser.add_argument("--script", type=Path, required=True, help="Path to script JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for images")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation")
    args = parser.parse_args()

    result = generate_from_script(args.script, args.output_dir, args.landscape)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()