"""A scanned PDF with a tiny-but-clean text layer (e.g. just the TOC) must trigger
the same PyMuPDF -> OCR rescue cascade as corrupt text. Eat That Frog (book #7) was
106 pages of scans with a 1,958-word TOC layer, and _extract happily returned it."""
import types

import pytest

from cogni import convert as conv


class _FakeResult:
    def __init__(self, text):
        self.text_content = text


def _fake_markitdown(monkeypatch, text):
    class _MD:
        def convert(self, _):
            return _FakeResult(text)
    monkeypatch.setattr(conv, "MarkItDown", _MD)


# a clean, plausible TOC — short, not corrupt, not doubled
_TOC = ("Set The Table Plan Every Day in Advance Apply the Rule to Everything " * 60)
_BOOK = ("Your frog is your biggest most important task, the one you are most likely "
         "to procrastinate on if you do not do something about it right now. " * 800)


def test_short_pdf_text_falls_through_to_ocr(monkeypatch, tmp_path):
    src = tmp_path / "book.pdf"
    src.write_bytes(b"%PDF-fake")
    _fake_markitdown(monkeypatch, _TOC)                       # ~short, clean
    monkeypatch.setattr(conv, "_pdf_text_pymupdf", lambda p: _TOC)   # fitz no better
    monkeypatch.setattr(conv, "_ocr_pdf", lambda p: _BOOK)           # OCR rescues
    assert conv._extract(src) == _BOOK.strip()


def test_short_pdf_rescued_by_pymupdf_without_ocr(monkeypatch, tmp_path):
    src = tmp_path / "book.pdf"
    src.write_bytes(b"%PDF-fake")
    _fake_markitdown(monkeypatch, _TOC)
    # the real _pdf_text_pymupdf returns stripped text — the fake must match
    monkeypatch.setattr(conv, "_pdf_text_pymupdf", lambda p: _BOOK.strip())
    monkeypatch.setattr(
        conv, "_ocr_pdf",
        lambda p: (_ for _ in ()).throw(AssertionError("OCR should not run")),
    )
    assert conv._extract(src) == _BOOK.strip()


def test_normal_length_pdf_is_untouched(monkeypatch, tmp_path):
    src = tmp_path / "book.pdf"
    src.write_bytes(b"%PDF-fake")
    _fake_markitdown(monkeypatch, _BOOK)
    monkeypatch.setattr(
        conv, "_pdf_text_pymupdf",
        lambda p: (_ for _ in ()).throw(AssertionError("rescue should not run")),
    )
    assert conv._extract(src) == _BOOK.strip()
