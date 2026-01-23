#!/usr/bin/env python3
"""
Extract 3-5 word hook from script for thumbnail.

Usage:
    python extract_thumbnail_hook.py --script midform.json
"""

import argparse
import json
import re
from pathlib import Path


def extract_hook(script_data: dict) -> str:
    """Extract the most impactful 3-5 word phrase for thumbnail."""
    # Try to get from existing hook
    if "hook" in script_data:
        hook = script_data["hook"]
        # Shorten to 3-5 words if needed
        words = hook.split()
        if len(words) > 5:
            return " ".join(words[:5])
        return hook

    # Try to get from title
    if "title" in script_data:
        title = script_data["title"]
        # Remove common prefixes/suffixes
        title = re.sub(r'^(how to|why|the|a|an)\s+', '', title, flags=re.IGNORECASE)
        words = title.split()
        if 3 <= len(words) <= 5:
            return title
        if len(words) > 5:
            return " ".join(words[:5])

    # Try to extract from first chapter
    if "chapters" in script_data and script_data["chapters"]:
        first_chapter = script_data["chapters"][0]
        chapter_title = first_chapter.get("title", "")
        if chapter_title:
            words = chapter_title.split()
            if len(words) <= 5:
                return chapter_title
            return " ".join(words[:5])

    # Fallback
    return "Transform Your Mind"


def main():
    parser = argparse.ArgumentParser(description="Extract thumbnail hook")
    parser.add_argument("--script", type=Path, required=True)
    args = parser.parse_args()

    with open(args.script) as f:
        script_data = json.load(f)

    hook = extract_hook(script_data)
    print(json.dumps({"hook": hook, "word_count": len(hook.split())}, indent=2))


if __name__ == "__main__":
    main()