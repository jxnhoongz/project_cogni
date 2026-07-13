"""Stage 0: convert — book file (PDF/epub/docx/...) -> projects/<slug>/book.md.

markitdown does the extraction. This stage validates the input, creates+activates
the book's project, converts, and caches book.md. Font-locked / scanned PDFs whose
text extracts as garbage are detected and re-run through OCR (tesseract) rather than
silently producing a broken script.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

from markitdown import MarkItDown

from .config import create_project, load_config, resolve_path, set_active_project, slugify

# Plain-text inputs are already text — read them directly. markitdown's text
# converter assumes ASCII and fails on non-ASCII bytes, so don't route them through it.
PLAIN_TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
# Structured/binary formats markitdown extracts text from.
MARKITDOWN_SUFFIXES = {".pdf", ".epub", ".docx", ".doc", ".html", ".htm"}
SUPPORTED_SUFFIXES = PLAIN_TEXT_SUFFIXES | MARKITDOWN_SUFFIXES

_WORDLIKE = re.compile(r"[A-Za-z][A-Za-z'’.\-]{1,}")


def _read_plain_text(path: Path) -> str:
    """Read a text file as UTF-8, falling back to latin-1 rather than crashing."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _looks_corrupt(text: str) -> bool:
    """True if extraction looks like a font-locked/scrambled PDF (unusable as text)."""
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.count("(cid:") >= 10:          # pdfminer marker for unmapped glyphs
        return True
    words = stripped.split()
    if not words:
        return True
    if len(stripped) / len(words) > 25:         # words run together — spaces lost
        return True
    if len(words) >= 50:
        wordlike = sum(1 for w in words if _WORDLIKE.fullmatch(w))
        if wordlike / len(words) < 0.35:        # very few real-looking words
            return True
    return False


def _ocr_pdf(src: Path, dpi: int = 300) -> str:
    """Rasterize each PDF page and OCR it with tesseract (via PyMuPDF + pytesseract)."""
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "OCR needs pymupdf + pytesseract and the tesseract binary. "
            "Install: pip install pymupdf pytesseract, plus the tesseract binary "
            "(`winget install UB-Mannheim.TesseractOCR` on Windows, "
            "`brew install tesseract` on macOS, `apt install tesseract-ocr` on Linux)."
        ) from e
    doc = fitz.open(str(src))
    parts: list[str] = []
    n = doc.page_count
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        parts.append(pytesseract.image_to_string(img))
        print(f"[convert] OCR page {i}/{n} ...", end="\r", flush=True)
    doc.close()
    print()
    return "\n\n".join(parts)


def _extract(src: Path) -> str:
    """Extract text from a supported book file, using OCR to rescue broken PDFs."""
    if src.suffix.lower() in PLAIN_TEXT_SUFFIXES:
        return _read_plain_text(src).strip()

    try:
        result = MarkItDown().convert(str(src))
    except Exception as e:
        raise RuntimeError(f"markitdown failed to convert {src}: {e}") from e
    text = (result.text_content or "").strip()

    if _looks_corrupt(text):
        if src.suffix.lower() != ".pdf":
            raise RuntimeError(
                f"{src.name}: extracted text looks corrupt/unreadable. "
                "Try an epub or a text-based source."
            )
        print("[convert] text looks font-locked/scanned — running OCR (this is slow) ...")
        text = _ocr_pdf(src).strip()
        if _looks_corrupt(text):
            raise RuntimeError(
                f"{src.name}: could not extract readable text even with OCR. "
                "Try an epub or a text-based PDF."
            )
    return text


def convert(
    source: str | Path,
    *,
    force: bool = False,
    cfg: dict[str, Any] | None = None,
) -> Path:
    """Convert a book file to markdown at the active book's book.md.

    Creates + activates a project named after the file. Cached: if book.md exists
    and force=False it's kept. Raises on missing/unsupported/unreadable input.
    """
    cfg = cfg or load_config()
    src = Path(source).expanduser()
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    if not src.is_file():
        raise ValueError(f"Source is not a file: {src}")
    if src.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported file type '{src.suffix}'. Supported: {supported}")

    # Each book is its own project, keyed by a slug of the filename.
    slug = slugify(src.stem)
    create_project(slug)
    set_active_project(slug)
    print(f"[convert] book '{slug}' is now the active project.")

    book_md = resolve_path(cfg, "book_md")
    if book_md.exists() and not force:
        print(f"[convert] cached — {book_md} exists (use --force to overwrite)")
        return book_md

    book_md.parent.mkdir(parents=True, exist_ok=True)
    text = _extract(src)
    if not text:
        raise RuntimeError(f"Conversion of {src} produced no text.")

    book_md.write_text(text + "\n", encoding="utf-8")
    print(f"[convert] {src.name} -> {book_md} ({len(text.split()):,} words)")
    return book_md
