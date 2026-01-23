#!/usr/bin/env python3
"""
Generate optimized title variants for YouTube video.

Usage:
    python generate_titles.py --script script.json --count 3
"""

import argparse
import json
import re
from pathlib import Path


def generate_title_variants(script_data: dict, count: int) -> list:
    """Generate multiple title variants from script data."""
    # Extract key elements
    hook = script_data.get("hook", "")
    title = script_data.get("title", "")
    book_title = script_data.get("book_title", "")
    angle = script_data.get("angle", "")

    variants = []

    # Variant 1: Hook-based (if short enough)
    if hook and len(hook) <= 60:
        # Clean up and make title-case
        hook_title = hook.strip().rstrip(".")
        if not hook_title.endswith(("?", "!")):
            hook_title += "."
        variants.append(hook_title)

    # Variant 2: Problem-solution
    if title:
        variants.append(title[:60])

    # Variant 3: Question format
    if angle:
        question = f"Why {angle.title()} Changes Everything"
        if len(question) <= 60:
            variants.append(question)

    # Variant 4: Book-focused
    if book_title:
        book_variant = f"{book_title}: The Key Insight Most Miss"
        if len(book_variant) <= 60:
            variants.append(book_variant)

    # Fallback variants
    fallbacks = [
        "The One Mindset Shift That Changes Everything",
        "This Changes How You Think About Success",
        "What No One Tells You About Building Habits"
    ]

    while len(variants) < count:
        for fb in fallbacks:
            if fb not in variants:
                variants.append(fb)
                break
        else:
            break

    return variants[:count]


def main():
    parser = argparse.ArgumentParser(description="Generate title variants")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()

    with open(args.script) as f:
        script_data = json.load(f)

    titles = generate_title_variants(script_data, args.count)

    print(json.dumps({
        "titles": titles,
        "count": len(titles),
        "all_under_60_chars": all(len(t) <= 60 for t in titles)
    }, indent=2))


if __name__ == "__main__":
    main()