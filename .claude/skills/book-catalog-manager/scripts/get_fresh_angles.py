#!/usr/bin/env python3
"""
Get unused angles for a book (not used in last 14 days).

Usage:
    python get_fresh_angles.py --book-id bk_0001 [--catalog PATH]
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).parent.parent.parent.parent.parent / "cognilab" / "catalog" / "books.json"
ANGLE_COOLDOWN_DAYS = 14


def load_catalog(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path) as f:
        return json.load(f)


def get_fresh_angles(catalog: dict, book_id: str) -> dict:
    """Return angles not used in the last 14 days."""
    book = next((b for b in catalog.get("books", []) if b["id"] == book_id), None)

    if not book:
        return {"error": f"Book not found: {book_id}"}

    all_angles = set(book.get("angle_library", []))
    if not all_angles:
        return {"error": "No angles in angle_library", "suggestion": "Add angles to book"}

    # Get recently used angles
    cutoff = datetime.now() - timedelta(days=ANGLE_COOLDOWN_DAYS)
    recent_angles = set()

    for format_type in ["shorts", "midform"]:
        coverage = book.get("coverage", {}).get(format_type, [])
        for video in coverage:
            pub_date = datetime.fromisoformat(video["published"].replace("Z", "+00:00")).replace(tzinfo=None)
            if pub_date > cutoff:
                recent_angles.add(video.get("angle", "").lower())

    # Filter to fresh angles
    fresh = [a for a in all_angles if a.lower() not in recent_angles]

    if not fresh:
        return {
            "book_id": book_id,
            "fresh_angles": [],
            "all_angles_used_recently": True,
            "suggestion": "Wait or add new angles to angle_library"
        }

    return {
        "book_id": book_id,
        "title": book["title"],
        "fresh_angles": fresh,
        "recently_used": list(recent_angles)
    }


def main():
    parser = argparse.ArgumentParser(description="Get fresh angles for book")
    parser.add_argument("--book-id", required=True)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = get_fresh_angles(catalog, args.book_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
