#!/usr/bin/env python3
"""
Check if a book is oversaturated (>3 uses in 30 days).

Usage:
    python check_oversaturation.py --book-id bk_0001 [--catalog PATH]
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).parent.parent.parent.parent.parent / "cognilab" / "catalog" / "books.json"
MAX_USES_30_DAYS = 3


def load_catalog(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path) as f:
        return json.load(f)


def check_oversaturation(catalog: dict, book_id: str) -> dict:
    """Check if book has been used too frequently."""
    book = next((b for b in catalog.get("books", []) if b["id"] == book_id), None)

    if not book:
        return {"error": f"Book not found: {book_id}"}

    cutoff = datetime.now() - timedelta(days=30)
    uses = 0

    for format_type in ["shorts", "midform"]:
        coverage = book.get("coverage", {}).get(format_type, [])
        for video in coverage:
            pub_date = datetime.fromisoformat(video["published"].replace("Z", "+00:00")).replace(tzinfo=None)
            if pub_date > cutoff:
                uses += 1

    return {
        "book_id": book_id,
        "title": book["title"],
        "oversaturated": uses >= MAX_USES_30_DAYS,
        "uses_last_30d": uses,
        "max_allowed": MAX_USES_30_DAYS
    }


def main():
    parser = argparse.ArgumentParser(description="Check book oversaturation")
    parser.add_argument("--book-id", required=True)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = check_oversaturation(catalog, args.book_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
