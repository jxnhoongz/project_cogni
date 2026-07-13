"""Configuration and paths.

Loads config.yaml (pipeline settings) and .env (secrets). Fails loudly on
missing files or missing keys — never silently defaults a secret.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root = the directory that contains config.yaml (one level up from this file).
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
STYLE_PATH = ROOT / "docs" / "STYLE.md"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load and lightly validate config.yaml. Raises on missing/invalid file."""
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"config.yaml did not parse to a mapping: {cfg_path}")
    for section in ("llm", "image", "video", "paths"):
        if section not in cfg:
            raise ValueError(f"config.yaml missing required section: '{section}'")
    return cfg


def resolve_path(cfg: dict[str, Any], key: str) -> Path:
    """Resolve a named path from config['paths'] to an absolute Path under ROOT."""
    paths = cfg.get("paths", {})
    if key not in paths:
        raise KeyError(f"config.yaml paths.{key} is not defined")
    return ROOT / paths[key]


def require_env(name: str) -> str:
    """Return an environment variable's value or fail loudly.

    Treats empty and known placeholder values as missing.
    """
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
    """Read the single STYLE token from docs/STYLE.md (fenced code block)."""
    if not STYLE_PATH.exists():
        raise FileNotFoundError(f"docs/STYLE.md not found at {STYLE_PATH}")
    text = STYLE_PATH.read_text(encoding="utf-8")
    # The token is the first fenced code block; may span multiple lines, which we
    # collapse to a single space-joined string for appending to an image prompt.
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
