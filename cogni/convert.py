"""Stage 0: convert — book file (PDF/epub/docx/...) -> input/book.md.

markitdown does the extraction. This stage only validates the input, runs the
conversion, and caches the result to disk so later stages read plain markdown.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from markitdown import MarkItDown

from .config import load_config, resolve_path

# Plain-text inputs are already text — read them directly. markitdown's text
# converter assumes ASCII and fails on non-ASCII bytes, so don't route them through it.
PLAIN_TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
# Structured/binary formats markitdown extracts text from.
MARKITDOWN_SUFFIXES = {".pdf", ".epub", ".docx", ".doc", ".html", ".htm"}
SUPPORTED_SUFFIXES = PLAIN_TEXT_SUFFIXES | MARKITDOWN_SUFFIXES


def _read_plain_text(path: Path) -> str:
    """Read a text file as UTF-8, falling back to latin-1 rather than crashing."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def convert(
    source: str | Path,
    *,
    force: bool = False,
    cfg: dict[str, Any] | None = None,
) -> Path:
    """Convert a book file to markdown at config paths.book_md (input/book.md).

    Cached: if book.md already exists and force=False, the existing file is kept.
    Returns the path to book.md. Raises on missing/unsupported/empty input.
    """
    cfg = cfg or load_config()
    src = Path(source).expanduser()
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    if not src.is_file():
        raise ValueError(f"Source is not a file: {src}")
    if src.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(
            f"Unsupported file type '{src.suffix}'. Supported: {supported}"
        )

    book_md = resolve_path(cfg, "book_md")
    if book_md.exists() and not force:
        print(f"[convert] cached — {book_md} exists (use --force to overwrite)")
        return book_md

    book_md.parent.mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() in PLAIN_TEXT_SUFFIXES:
        text = _read_plain_text(src).strip()
    else:
        try:
            result = MarkItDown().convert(str(src))
        except Exception as e:
            raise RuntimeError(f"markitdown failed to convert {src}: {e}") from e
        text = (result.text_content or "").strip()
    if not text:
        raise RuntimeError(
            f"Conversion of {src} produced no text (scanned/image-only PDF?)."
        )

    book_md.write_text(text + "\n", encoding="utf-8")
    words = len(text.split())
    print(f"[convert] {src.name} -> {book_md} ({words:,} words)")
    return book_md
