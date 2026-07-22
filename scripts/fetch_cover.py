"""Fetch a book's cover image from a LEGAL public API — no login, no shadow library.

Open Library's cover service (covers.openlibrary.org) and Google Books both expose cover
thumbnails by title/ISBN for free. The cover art therefore never depends on how we sourced
the book text; it's a separate, clean input for the Remotion book-intro overlay.

    python scripts/fetch_cover.py "Man's Search for Meaning" [--author Frankl] [--out path.jpg]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "project-cogni/1.0 (book-review channel; cover lookup)"}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _openlibrary(title: str, author: str | None) -> str | None:
    """Search Open Library, return a cover URL (large) for the best match, or None."""
    q = {"title": title, "limit": 5}
    if author:
        q["author"] = author
    url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(q)
    data = json.loads(_get(url))
    for doc in data.get("docs", []):
        cid = doc.get("cover_i")
        if cid:
            return f"https://covers.openlibrary.org/b/id/{cid}-L.jpg"
        for isbn in (doc.get("isbn") or [])[:1]:
            return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    return None


def _googlebooks(title: str, author: str | None) -> str | None:
    q = title + (f" inauthor:{author}" if author else "")
    url = "https://www.googleapis.com/books/v1/volumes?q=" + urllib.parse.quote(q)
    data = json.loads(_get(url))
    for item in data.get("items", []):
        links = (item.get("volumeInfo") or {}).get("imageLinks") or {}
        u = links.get("thumbnail") or links.get("smallThumbnail")
        if u:
            return u.replace("http://", "https://").replace("&edge=curl", "") + "&fife=w800"
    return None


def fetch_cover(title: str, author: str | None, out: Path) -> Path:
    for name, fn in (("openlibrary", _openlibrary), ("googlebooks", _googlebooks)):
        try:
            u = fn(title, author)
        except Exception as e:
            print(f"[cover] {name} lookup failed: {e}")
            continue
        if not u:
            print(f"[cover] {name}: no cover found")
            continue
        try:
            img = _get(u)
        except Exception as e:
            print(f"[cover] {name} download failed: {e}")
            continue
        if len(img) < 2000:                       # OL returns a tiny blank on a miss
            print(f"[cover] {name}: returned a blank/placeholder, skipping")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(img)
        print(f"[cover] {name} -> {out} ({len(img)//1024} KB)")
        return out
    raise SystemExit(f"no cover found for {title!r} (try passing --author, or a different title)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--author", default=None)
    ap.add_argument("--out", default=None, help="output path (default: remotion/public/cover.jpg)")
    a = ap.parse_args()
    out = Path(a.out) if a.out else Path(__file__).resolve().parent.parent / "remotion" / "public" / "cover.jpg"
    fetch_cover(a.title, a.author, out)


if __name__ == "__main__":
    sys.exit(main())
