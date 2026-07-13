"""Stage 1: ingest — input/book.md -> outline.json.

A cheap-model pass that reads the book and extracts the essential structure:
title, author, a one-paragraph thesis, and 6-12 key ideas. Later stages turn
those ideas into scenes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_config, resolve_path
from .llm import call_llm

_SYSTEM = (
    "You are a careful editor. You read a book and distill its essential "
    "structure: what it is, its central argument, and its most important ideas. "
    "You return only valid JSON."
)


def _budget_text(text: str, max_chars: int) -> tuple[str, bool]:
    """Return text within max_chars. If longer, sample evenly across the whole
    book so ideas from beginning, middle, and end are all represented.

    Returns (text, was_sampled).
    """
    if len(text) <= max_chars:
        return text, False
    # Even sampling: take N windows spread across the document.
    windows = 12
    win = max_chars // windows
    step = len(text) // windows
    parts = [text[i * step : i * step + win] for i in range(windows)]
    return "\n\n[...]\n\n".join(parts), True


def _build_prompt(book_text: str, min_ideas: int, max_ideas: int) -> str:
    return (
        f"Read the following book text and extract its structure as JSON with "
        f"exactly these fields:\n"
        f'  "title": the book\'s title (string)\n'
        f'  "author": the author, or "" if unclear (string)\n'
        f'  "thesis": the central argument in 2-4 sentences (string)\n'
        f'  "key_ideas": an array of {min_ideas}-{max_ideas} objects, each with '
        f'"title" (a short label, 3-6 words) and "summary" (2-4 sentences '
        f"explaining the idea in plain language).\n\n"
        f"Order key_ideas from most to least central. Ignore front/back matter "
        f"(license, table of contents, publisher notes).\n\n"
        f"BOOK TEXT:\n{book_text}"
    )


def ingest(*, force: bool = False, cfg: dict[str, Any] | None = None) -> Path:
    """Read input/book.md, extract an outline, write outline.json.

    Cached: if outline.json exists and force=False, it is kept.
    """
    cfg = cfg or load_config()
    book_md = resolve_path(cfg, "book_md")
    if not book_md.exists():
        raise FileNotFoundError(
            f"{book_md} not found — run `convert` first to create it."
        )

    outline_path = resolve_path(cfg, "outline")
    if outline_path.exists() and not force:
        print(f"[ingest] cached — {outline_path} exists (use --force to overwrite)")
        return outline_path

    ing = cfg["ingest"]
    text = book_md.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"{book_md} is empty.")

    book_text, sampled = _budget_text(text, ing["max_input_chars"])
    if sampled:
        print(
            f"[ingest] book is large ({len(text):,} chars) — evenly sampled to "
            f"~{len(book_text):,} chars across the whole book."
        )

    model = cfg["llm"]["models"]["ingest"]
    print(f"[ingest] extracting outline with {model} ...")
    data = call_llm(
        model,
        _build_prompt(book_text, ing["min_ideas"], ing["max_ideas"]),
        system=_SYSTEM,
        json_out=True,
        cfg=cfg,
    )

    outline = _validate(data, ing["min_ideas"], ing["max_ideas"])
    outline_path.write_text(
        json.dumps(outline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[ingest] {outline_path} — \"{outline['title']}\", "
        f"{len(outline['key_ideas'])} key ideas."
    )
    return outline_path


def _validate(data: dict[str, Any], min_ideas: int, max_ideas: int) -> dict[str, Any]:
    """Check the model returned the expected shape; raise a clear error if not."""
    if not isinstance(data, dict):
        raise RuntimeError("ingest: model did not return a JSON object")
    title = str(data.get("title") or "").strip()
    thesis = str(data.get("thesis") or "").strip()
    ideas = data.get("key_ideas")
    if not title:
        raise RuntimeError("ingest: model returned no title")
    if not thesis:
        raise RuntimeError("ingest: model returned no thesis")
    if not isinstance(ideas, list) or not ideas:
        raise RuntimeError("ingest: model returned no key_ideas")

    clean_ideas = []
    for i, idea in enumerate(ideas, 1):
        if not isinstance(idea, dict):
            raise RuntimeError(f"ingest: key_idea #{i} is not an object")
        it = str(idea.get("title") or "").strip()
        su = str(idea.get("summary") or "").strip()
        if not it or not su:
            raise RuntimeError(f"ingest: key_idea #{i} missing title or summary")
        clean_ideas.append({"title": it, "summary": su})

    if len(clean_ideas) < min_ideas:
        # Warn but don't fail — the book may genuinely have fewer distinct ideas.
        print(
            f"[ingest] warning: only {len(clean_ideas)} key ideas "
            f"(expected >= {min_ideas})."
        )

    return {
        "title": title,
        "author": str(data.get("author") or "").strip(),
        "thesis": thesis,
        "key_ideas": clean_ideas[:max_ideas],
    }
