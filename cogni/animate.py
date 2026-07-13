"""Higgsfield hero-clip helpers.

The image->video generation itself runs via the Higgsfield MCP (driven by Claude
using the `cogni-animate` skill). These functions just say WHAT to animate and
WHERE the result goes, and wire a finished clip into scenes.json so `assemble`
uses it. Only scenes flagged animate=true get a hero clip; the rest stay stills.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import httpx

from .config import load_config, project_root, resolve_path


def _load(cfg: dict[str, Any]) -> dict[str, Any]:
    p = resolve_path(cfg, "scenes")
    if not p.exists():
        raise FileNotFoundError(f"{p} not found — run `script` first.")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not doc.get("scenes"):
        raise RuntimeError(f"{p} has no scenes.")
    return doc


def animate_plan(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Scenes flagged animate=true: their still, target clip path, and status."""
    cfg = cfg or load_config()
    doc = _load(cfg)
    images_dir = resolve_path(cfg, "images")
    clips_dir = resolve_path(cfg, "clips")
    plan = []
    for s in doc["scenes"]:
        if not s.get("animate"):
            continue
        img = images_dir / f"scene_{s['id']:03d}.png"
        clip = clips_dir / f"scene_{s['id']:03d}.mp4"
        plan.append(
            {
                "id": s["id"],
                "image": str(img) if img.exists() else None,
                "clip": str(clip),
                "has_clip": clip.exists(),
                "narration": s.get("narration") or s.get("narration_en", ""),
                "image_prompt": s.get("image_prompt", ""),
            }
        )
    return plan


def save_clip(scene_id: int, source: str, cfg: dict[str, Any] | None = None) -> Path:
    """Save a generated hero clip (local path or https URL from Higgsfield) to
    clips/scene_XXX.mp4 and record clip_path in scenes.json."""
    cfg = cfg or load_config()
    clips_dir = resolve_path(cfg, "clips")
    clips_dir.mkdir(parents=True, exist_ok=True)
    out = clips_dir / f"scene_{int(scene_id):03d}.mp4"

    src = str(source)
    if src.startswith(("http://", "https://")):
        r = httpx.get(src, timeout=300, follow_redirects=True)
        r.raise_for_status()
        out.write_bytes(r.content)
    else:
        shutil.copyfile(src, out)

    scenes_path = resolve_path(cfg, "scenes")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    rel = str(out.relative_to(project_root(cfg)))
    for s in doc["scenes"]:
        if s["id"] == int(scene_id):
            s["clip_path"] = rel
    scenes_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out
