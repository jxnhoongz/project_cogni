"""check-audio — verify every scene in scenes.json has a recorded audio file.

The [MANUAL] recording step lives between `script` and `images`. This tells the
user exactly which scenes still need a recording, and records the found path back
into scenes.json so later stages know where the audio is.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_config, resolve_path

AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac")


def _find_audio(audio_dir: Path, scene_id: int) -> Path | None:
    """Look for audio/scene_NNN.<ext> in preference order."""
    stem = f"scene_{scene_id:03d}"
    for ext in AUDIO_EXTS:
        candidate = audio_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def check_audio(*, cfg: dict[str, Any] | None = None) -> bool:
    """Report which scenes have/need audio; write found paths into scenes.json.

    Returns True only if every scene has a matching audio file.
    """
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(
            f"{scenes_path} not found — run `script` first to create it."
        )
    audio_dir = resolve_path(cfg, "audio")

    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    present = 0
    changed = False
    for s in scenes:
        found = _find_audio(audio_dir, s["id"])
        if found:
            present += 1
            rel = str(found.relative_to(resolve_path(cfg, "input").parent))
            if s.get("audio_path") != rel:
                s["audio_path"] = rel
                changed = True
            print(f"  scene {s['id']:>2}: ✓ {rel}")
        else:
            if s.get("audio_path") is not None:
                s["audio_path"] = None
                changed = True
            print(f"  scene {s['id']:>2}: ✗ missing (expected {audio_dir.name}/scene_{s['id']:03d}.wav)")

    if changed:
        scenes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    total = len(scenes)
    print(f"[check-audio] {present}/{total} scenes have audio.")
    return present == total
