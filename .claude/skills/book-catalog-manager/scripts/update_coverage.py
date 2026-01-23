#!/usr/bin/env python3
"""
Update book coverage after publishing a video.

Usage:
    python update_coverage.py --book-id bk_0001 --video-id S_20251012_01 --angle "identity-based habits" --format shorts [--catalog PATH]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).parent.parent.parent.parent.parent / "cognilab" / "catalog" / "books.json"


def load_catalog(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path) as f:
        return json.load(f)


def save_catalog(path: Path, catalog: dict):
    with open(path, "w") as f:
        json.dump(catalog, f, indent=2)


def update_coverage(catalog: dict, book_id: str, video_id: str, angle: str, format_type: str) -> dict:
    """Add video to book's coverage history."""
    book = next((b for b in catalog.get("books", []) if b["id"] == book_id), None)

    if not book:
        return {"error": f"Book not found: {book_id}"}

    # Initialize coverage if needed
    if "coverage" not in book:
        book["coverage"] = {"shorts": [], "midform": []}
    if format_type not in book["coverage"]:
        book["coverage"][format_type] = []

    # Add new entry
    now = datetime.now().isoformat() + "Z"
    book["coverage"][format_type].append({
        "id": video_id,
        "angle": angle,
        "published": now
    })

    # Update last_used
    book["last_used"] = now[:10]  # YYYY-MM-DD

    return {
        "success": True,
        "book_id": book_id,
        "video_id": video_id,
        "angle": angle,
        "format": format_type,
        "published": now
    }


def main():
    parser = argparse.ArgumentParser(description="Update book coverage")
    parser.add_argument("--book-id", required=True)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--angle", required=True)
    parser.add_argument("--format", required=True, choices=["shorts", "midform"])
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = update_coverage(catalog, args.book_id, args.video_id, args.angle, args.format)

    if "error" not in result:
        save_catalog(args.catalog, catalog)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
