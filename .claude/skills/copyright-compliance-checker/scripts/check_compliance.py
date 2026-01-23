#!/usr/bin/env python3
"""
Check script for copyright compliance.

Usage:
    python check_compliance.py --script script.json
"""

import argparse
import json
import re
from pathlib import Path

MAX_QUOTE_LENGTH = 50
MAX_TOTAL_QUOTED = 300
QUOTE_PATTERN = r'"([^"]+)"'


def extract_quotes(text: str) -> list:
    """Extract quoted text from script."""
    return re.findall(QUOTE_PATTERN, text)


def count_words(text: str) -> int:
    return len(text.split())


def check_attribution(text: str, book_title: str = None, author: str = None) -> bool:
    """Check if book/author is mentioned."""
    text_lower = text.lower()

    # Generic attribution patterns
    has_attribution = any([
        "according to" in text_lower,
        "in the book" in text_lower,
        "author" in text_lower,
        "writes" in text_lower,
        "says" in text_lower,
    ])

    # Specific book/author mention
    if book_title:
        has_attribution = has_attribution or book_title.lower() in text_lower
    if author:
        has_attribution = has_attribution or author.lower() in text_lower

    return has_attribution


def check_transformative(text: str) -> bool:
    """Check if content is transformative (has analysis, not just summary)."""
    text_lower = text.lower()

    analysis_indicators = [
        "this means",
        "in other words",
        "the key insight",
        "what this teaches",
        "here's why",
        "the problem with",
        "the benefit",
        "you can apply",
        "try this",
        "for example",
        "imagine",
        "think about",
        "this connects to",
        "my take",
        "practically speaking",
    ]

    count = sum(1 for indicator in analysis_indicators if indicator in text_lower)
    return count >= 3  # At least 3 analysis indicators


def check_compliance(script_data: dict) -> dict:
    """Run all compliance checks."""
    # Get script text
    if "script" in script_data:
        text = script_data["script"]
    elif "chapters" in script_data:
        text = " ".join(ch.get("script", "") for ch in script_data["chapters"])
    else:
        text = json.dumps(script_data)

    # Extract quotes
    quotes = extract_quotes(text)
    quote_lengths = [count_words(q) for q in quotes]
    longest_quote = max(quote_lengths) if quote_lengths else 0
    total_quoted = sum(quote_lengths)

    # Run checks
    checks = {
        "long_quotes": {
            "passed": longest_quote <= MAX_QUOTE_LENGTH,
            "longest": longest_quote,
            "max_allowed": MAX_QUOTE_LENGTH,
            "quotes_over_limit": [q for q, l in zip(quotes, quote_lengths) if l > MAX_QUOTE_LENGTH]
        },
        "total_quoted": {
            "passed": total_quoted <= MAX_TOTAL_QUOTED,
            "words": total_quoted,
            "max_allowed": MAX_TOTAL_QUOTED
        },
        "has_attribution": {
            "passed": check_attribution(
                text,
                script_data.get("book_title"),
                script_data.get("author")
            )
        },
        "is_transformative": {
            "passed": check_transformative(text)
        }
    }

    # Determine risk level
    issues = []
    risk_level = "low"

    if not checks["long_quotes"]["passed"]:
        issues.append(f"Quote too long: {longest_quote} words (max {MAX_QUOTE_LENGTH})")
        risk_level = "high"

    if not checks["total_quoted"]["passed"]:
        issues.append(f"Too much quoted content: {total_quoted} words (max {MAX_TOTAL_QUOTED})")
        risk_level = "medium" if risk_level == "low" else risk_level

    if not checks["has_attribution"]["passed"]:
        issues.append("Missing book/author attribution")
        risk_level = "high"

    if not checks["is_transformative"]["passed"]:
        issues.append("Content may not be sufficiently transformative")
        risk_level = "medium" if risk_level == "low" else risk_level

    compliant = len([i for i in issues if "high" in risk_level or "too long" in i.lower()]) == 0

    return {
        "compliant": compliant,
        "risk_level": risk_level,
        "checks": checks,
        "issues": issues,
        "recommendations": get_recommendations(checks)
    }


def get_recommendations(checks: dict) -> list:
    """Generate fix recommendations for failed checks."""
    recs = []

    if not checks["long_quotes"]["passed"]:
        recs.append("Shorten quotes to <50 words or paraphrase")

    if not checks["total_quoted"]["passed"]:
        recs.append("Reduce total quoted content, add more original analysis")

    if not checks["has_attribution"]["passed"]:
        recs.append("Add explicit book title and author mention")

    if not checks["is_transformative"]["passed"]:
        recs.append("Add more analysis, examples, and practical applications")

    return recs


def main():
    parser = argparse.ArgumentParser(description="Check copyright compliance")
    parser.add_argument("--script", type=Path, required=True)
    args = parser.parse_args()

    with open(args.script) as f:
        script_data = json.load(f)

    result = check_compliance(script_data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()