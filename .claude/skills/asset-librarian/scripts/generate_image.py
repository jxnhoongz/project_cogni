#!/usr/bin/env python3
"""
Generate AI image matching voiceover content in Da Vinci oil painting style.

Usage:
    python generate_image.py --text "The power of habits" --output scene.png
    python generate_image.py --text "A person reading" --output scene.png --landscape

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
    # Extract the visual concept from the text
    prompt = f"Visual representation of: {text}\n\nStyle: {DAVINCI_STYLE}"
    return prompt


def generate_image(text: str, output_path: Path, landscape: bool = False) -> dict:
    """Generate image using DALL-E 3 API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}

    prompt = create_prompt(text)

    # Portrait for shorts (9:16), landscape for midform (16:9)
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
        return {"error": f"API error: {response.status_code}", "detail": response.text}

    data = response.json()
    image_data = data["data"][0]["b64_json"]
    revised_prompt = data["data"][0].get("revised_prompt", prompt)

    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(image_data))

    image_id = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return {
        "id": image_id,
        "input_text": text,
        "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
        "revised_prompt": revised_prompt,
        "local_path": str(output_path),
        "size": size,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Da Vinci style image from text")
    parser.add_argument("--text", required=True, help="Voiceover text or scene description")
    parser.add_argument("--output", type=Path, required=True, help="Output image path")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation (for midform)")
    args = parser.parse_args()

    result = generate_image(args.text, args.output, args.landscape)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()