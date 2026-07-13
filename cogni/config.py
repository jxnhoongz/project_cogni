"""Configuration, projects, and paths.

Each book is a "project" — its own folder under projects/<slug>/ holding book.md,
outline.json, scenes.json, recording_script.txt, and images/ audio/ clips/ output/.
One project is "active" at a time (pointer in .active_project); every stage reads
and writes inside the active project. Background music lives at the repo level
(shared across books).

Loads config.yaml (pipeline settings) and .env (secrets). Fails loudly on missing
files, missing keys, or no active project.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
STYLE_PATH = ROOT / "docs" / "STYLE.md"
PROJECTS_DIR = ROOT / "projects"
ACTIVE_FILE = ROOT / ".active_project"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load and lightly validate config.yaml. Raises on missing/invalid file."""
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"config.yaml did not parse to a mapping: {cfg_path}")
    for section in ("llm", "image", "video", "paths", "shared"):
        if section not in cfg:
            raise ValueError(f"config.yaml missing required section: '{section}'")
    return cfg


# --- projects ---------------------------------------------------------------

def slugify(name: str) -> str:
    """A filesystem-safe book slug from a title or filename."""
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return s or "book"


def list_projects() -> list[str]:
    if not PROJECTS_DIR.exists():
        return []
    return sorted(p.name for p in PROJECTS_DIR.iterdir() if p.is_dir())


def create_project(slug: str) -> Path:
    d = PROJECTS_DIR / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def set_active_project(slug: str) -> None:
    ACTIVE_FILE.write_text(str(slug).strip() + "\n", encoding="utf-8")


def active_project() -> str | None:
    """The active book slug — from the pointer, or the sole project if unset."""
    if ACTIVE_FILE.exists():
        slug = ACTIVE_FILE.read_text(encoding="utf-8").strip()
        if slug and (PROJECTS_DIR / slug).is_dir():
            return slug
    projects = list_projects()
    return projects[0] if len(projects) == 1 else None


def project_root(cfg: dict[str, Any] | None = None) -> Path:
    """The active book's folder. Raises a clear error if none is active."""
    slug = active_project()
    if not slug:
        raise RuntimeError(
            "No active book. Upload/convert a book to create one, or pass "
            "--project <slug> (see `python main.py projects`)."
        )
    return PROJECTS_DIR / slug


def resolve_path(cfg: dict[str, Any], key: str) -> Path:
    """Resolve a per-project path from config['paths'] under the active book."""
    paths = cfg.get("paths", {})
    if key not in paths:
        raise KeyError(f"config.yaml paths.{key} is not defined")
    return project_root(cfg) / paths[key]


def resolve_shared(cfg: dict[str, Any], key: str) -> Path:
    """Resolve a repo-level shared path from config['shared'] (e.g. music)."""
    shared = cfg.get("shared", {})
    if key not in shared:
        raise KeyError(f"config.yaml shared.{key} is not defined")
    return ROOT / shared[key]


# --- secrets & style --------------------------------------------------------

def require_env(name: str) -> str:
    """Return an environment variable's value or fail loudly (empty/placeholder = missing)."""
    load_dotenv(ROOT / ".env")
    value = os.environ.get(name, "").strip()
    placeholder = (
        not value
        or value.startswith("sk-or-your")
        or value.startswith("your")
        or "your-key" in value
    )
    if placeholder:
        raise RuntimeError(
            f"Environment variable '{name}' is not set. "
            f"Add it to {ROOT / '.env'} (see .env.example)."
        )
    return value


def load_style_token() -> str:
    """Read the single STYLE token from docs/STYLE.md (first fenced block)."""
    if not STYLE_PATH.exists():
        raise FileNotFoundError(f"docs/STYLE.md not found at {STYLE_PATH}")
    text = STYLE_PATH.read_text(encoding="utf-8")
    in_fence = False
    collected: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if in_fence:
                break
            in_fence = True
            continue
        if in_fence:
            collected.append(line.strip())
    token = " ".join(part for part in collected if part).strip()
    if not token:
        raise ValueError("Could not find a STYLE token in docs/STYLE.md")
    return token
