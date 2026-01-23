#!/usr/bin/env python3
"""
Validate script against quality standards.

Usage:
    python validate_script.py --script script.json --format shorts|midform
"""

import argparse
import json
import re
from pathlib import Path

GENERIC_PHRASES = [
    r"in today's video",
    r"let's dive in",
    r"without further ado",
    r"hey guys",
    r"welcome back",
    r"don't forget to",
    r"smash that like",
    r"hit subscribe",
    r"let me know in the comments",
    r"so basically",
    r"you know what i mean",
]

VAGUE_ACTION_WORDS = [
    "think about",
    "consider",
    "reflect on",
    "be mindful",
    "try to",
    "maybe",
    "perhaps",
]

SHORTS_LIMITS = {"word_min": 130, "word_max": 260, "hook_max": 12}
MIDFORM_LIMITS = {"word_min": 8000, "word_max": 10000, "chapters_min": 4, "chapters_max": 5}


def count_words(text: str) -> int:
    return len(text.split())


def check_generic_phrases(text: str) -> list:
    found = []
    text_lower = text.lower()
    for phrase in GENERIC_PHRASES:
        if re.search(phrase, text_lower):
            found.append(phrase)
    return found


def check_action_step_specific(action: str) -> bool:
    action_lower = action.lower()
    for vague in VAGUE_ACTION_WORDS:
        if vague in action_lower:
            return False
    # Check for specificity indicators
    has_specific = any([
        re.search(r'\d+', action),  # Has numbers
        "today" in action_lower,
        "tomorrow" in action_lower,
        "morning" in action_lower,
        "write" in action_lower,
        "list" in action_lower,
    ])
    return has_specific or len(action.split()) >= 8


def calculate_readability(text: str) -> float:
    """Simple Flesch-Kincaid approximation."""
    words = text.split()
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    syllables = sum(count_syllables(w) for w in words)

    words_per_sentence = len(words) / sentences
    syllables_per_word = syllables / len(words) if words else 0

    # Flesch-Kincaid Grade Level
    return 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59


def count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    return max(1, count)


def validate_shorts(script_data: dict) -> dict:
    script = script_data.get("script", "")
    hook = script_data.get("hook", "")
    action_step = script_data.get("action_step", "")

    word_count = count_words(script)
    hook_words = count_words(hook)
    generic = check_generic_phrases(script)
    has_example = any(w in script.lower() for w in ["for example", "like when", "imagine", "picture this", "story"])

    checks = {
        "word_count": {
            "passed": SHORTS_LIMITS["word_min"] <= word_count <= SHORTS_LIMITS["word_max"],
            "value": word_count,
            "range": f"{SHORTS_LIMITS['word_min']}-{SHORTS_LIMITS['word_max']}"
        },
        "hook_length": {
            "passed": hook_words <= SHORTS_LIMITS["hook_max"],
            "value": hook_words,
            "max": SHORTS_LIMITS["hook_max"]
        },
        "generic_phrases": {
            "passed": len(generic) == 0,
            "found": generic
        },
        "has_example": {
            "passed": has_example
        },
        "action_step_specific": {
            "passed": check_action_step_specific(action_step)
        },
        "readability": {
            "passed": calculate_readability(script) <= 8,
            "score": round(calculate_readability(script), 1)
        }
    }

    passed = all(c["passed"] for c in checks.values())
    return {"passed": passed, "checks": checks, "action": "proceed" if passed else "fix_or_regenerate"}


def validate_midform(script_data: dict) -> dict:
    chapters = script_data.get("chapters", [])
    total_words = sum(count_words(ch.get("script", "")) for ch in chapters)

    checks = {
        "word_count": {
            "passed": MIDFORM_LIMITS["word_min"] <= total_words <= MIDFORM_LIMITS["word_max"],
            "value": total_words,
            "range": f"{MIDFORM_LIMITS['word_min']}-{MIDFORM_LIMITS['word_max']}"
        },
        "chapter_count": {
            "passed": MIDFORM_LIMITS["chapters_min"] <= len(chapters) <= MIDFORM_LIMITS["chapters_max"],
            "value": len(chapters),
            "range": f"{MIDFORM_LIMITS['chapters_min']}-{MIDFORM_LIMITS['chapters_max']}"
        },
        "has_experiment": {
            "passed": bool(script_data.get("seven_day_experiment"))
        }
    }

    passed = all(c["passed"] for c in checks.values())
    return {"passed": passed, "checks": checks, "action": "proceed" if passed else "fix_or_regenerate"}


def main():
    parser = argparse.ArgumentParser(description="Validate script quality")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--format", required=True, choices=["shorts", "midform"])
    args = parser.parse_args()

    with open(args.script) as f:
        script_data = json.load(f)

    if args.format == "shorts":
        result = validate_shorts(script_data)
    else:
        result = validate_midform(script_data)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()