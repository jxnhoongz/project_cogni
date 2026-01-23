#!/usr/bin/env python3
"""
Suggest next book for video based on freshness scoring.

Usage:
    python suggest_next_book.py --format shorts|midform [--catalog PATH]

Algorithm:
    - freshness = days_since_last_used / 30 (capped at 1.0)
    - Never used = 2.0 boost
    - >3 uses in 30 days = 0.1 penalty (oversaturated)
    - Returns weighted random selection favoring higher scores
"""

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).parent.parent.parent.parent.parent / "cognilab" / "catalog" / "books.json"


def load_catalog(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path) as f:
        return json.load(f)


def calculate_freshness(book: dict, format_type: str) -> float:
    """Calculate freshness score for a book (0.0-2.0)."""
    coverage = book.get("coverage", {}).get(format_type, [])

    if not coverage:
        return 2.0  # Never used = highest priority

    # Get most recent use
    last_used = book.get("last_used")
    if not last_used:
        return 2.0

    last_date = datetime.fromisoformat(last_used.replace("Z", "+00:00")).replace(tzinfo=None)
    days_since = (datetime.now() - last_date).days

    # Count uses in last 30 days
    cutoff = datetime.now() - timedelta(days=30)
    recent_uses = sum(
        1 for v in coverage
        if datetime.fromisoformat(v["published"].replace("Z", "+00:00")).replace(tzinfo=None) > cutoff
    )

    # Oversaturation penalty
    if recent_uses >= 3:
        return 0.1

    # Normal freshness decay
    return min(days_since / 30, 1.0)


def suggest_book(catalog: dict, format_type: str) -> dict:
    """Select book using weighted random based on freshness."""
    books = [b for b in catalog.get("books", []) if b.get("status") == "active"]

    if not books:
        return {"error": "No active books in catalog"}

    # Calculate scores
    scored = []
    for book in books:
        score = calculate_freshness(book, format_type)
        scored.append((book, score))

    # Weighted random selection
    total = sum(s for _, s in scored)
    if total == 0:
        return {"error": "All books oversaturated", "suggestion": "Add new books to catalog"}

    r = random.uniform(0, total)
    cumulative = 0
    for book, score in scored:
        cumulative += score
        if r <= cumulative:
            return {
                "book_id": book["id"],
                "title": book["title"],
                "authors": book.get("authors", []),
                "freshness": round(score, 2),
                "angle_library": book.get("angle_library", [])
            }

    # Fallback
    return scored[0][0]


def main():
    parser = argparse.ArgumentParser(description="Suggest next book for video")
    parser.add_argument("--format", required=True, choices=["shorts", "midform"])
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = suggest_book(catalog, args.format)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
