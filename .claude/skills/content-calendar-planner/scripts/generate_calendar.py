#!/usr/bin/env python3
"""
Generate publishing calendar for specified period.

Usage:
    python generate_calendar.py --days 7 --phase 1 [--energy normal|low] [--catalog PATH]
"""

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DEFAULT_CATALOG = Path(__file__).parent.parent.parent.parent.parent / "cognilab" / "catalog" / "books.json"

PHASE_CADENCE = {
    1: {"shorts_per_week": 3, "midform_per_week": 0.5},
    2: {"shorts_per_week": 5, "midform_per_week": 1},
    3: {"shorts_per_week": 7, "midform_per_week": 1.5}
}

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_catalog(path: Path) -> dict:
    if not path.exists():
        return {"books": []}
    with open(path) as f:
        return json.load(f)


def get_book_freshness(book: dict) -> float:
    last_used = book.get("last_used")
    if not last_used:
        return 1.0
    days = (datetime.now() - datetime.fromisoformat(last_used)).days
    return min(days / 30, 1.0)


def generate_calendar(catalog: dict, days: int, phase: int, energy: str) -> dict:
    cadence = PHASE_CADENCE.get(phase, PHASE_CADENCE[1])
    multiplier = 0.5 if energy == "low" else 1.0
    shorts_target = int(cadence["shorts_per_week"] * (days / 7) * multiplier)
    midform_target = int(cadence["midform_per_week"] * (days / 7) * multiplier)

    calendar = []
    start_date = datetime.now()
    books = [b for b in catalog.get("books", []) if b.get("status") == "active"]

    for i in range(shorts_target + midform_target):
        day_offset = i * (days // (shorts_target + midform_target + 1))
        date = start_date + timedelta(days=day_offset)
        format_type = "midform" if i < midform_target and date.weekday() >= 5 else "shorts"

        if books:
            book = random.choice(books)
            angle = random.choice(book.get("angle_library", ["general"]))
            calendar.append({
                "day": WEEKDAY_NAMES[date.weekday()],
                "date": date.strftime("%Y-%m-%d"),
                "format": format_type,
                "book_id": book["id"],
                "title": book["title"],
                "angle": angle
            })

    return {"calendar": calendar, "stats": {"shorts": shorts_target, "midform": midform_target}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--phase", type=int, required=True, choices=[1, 2, 3])
    parser.add_argument("--energy", default="normal", choices=["normal", "low"])
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    result = generate_calendar(catalog, args.days, args.phase, args.energy)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
