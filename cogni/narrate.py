"""Stage 3: narrate — scenes.json narration -> audio/scene_XXX.mp3 via TTS.

`generate_tts()` is a pluggable provider. Provider "edge" uses edge-tts (free,
no key). Later providers (OpenAI, ElevenLabs) slot in the same way. Cached: a
scene keeps its audio unless --force. Records audio_path back into scenes.json,
so `assemble` finds the narration.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from .config import load_config, project_root, resolve_path


def _edge_tts(text: str, voice: str, out_path: Path) -> None:
    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError("edge-tts not installed — `pip install edge-tts`.") from e

    async def _run() -> None:
        await edge_tts.Communicate(text, voice).save(str(out_path))

    asyncio.run(_run())


def generate_tts(text: str, out_path: Path, cfg: dict[str, Any]) -> None:
    """Synthesize `text` to speech at out_path, per config tts.provider."""
    provider = cfg["tts"]["provider"]
    if provider == "edge":
        _edge_tts(text, cfg["tts"]["voice"], out_path)
    else:
        raise RuntimeError(f"unknown tts provider '{provider}' (use 'edge')")


def narrate(*, force: bool = False, cfg: dict[str, Any] | None = None) -> Path:
    """Generate narration audio for every scene in scenes.json (cached)."""
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    audio_dir = resolve_path(cfg, "audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    root = project_root(cfg)
    provider = cfg["tts"]["provider"]
    voice = cfg["tts"].get("voice", "")

    made = cached = 0
    changed = False
    for s in scenes:
        out = audio_dir / f"scene_{s['id']:03d}.mp3"
        rel = str(out.relative_to(root))
        text = s.get("narration") or s.get("narration_en") or ""
        if not text.strip():
            print(f"[narrate] scene {s['id']:>2}: skipped (no narration text)")
            continue
        if out.exists() and not force:
            cached += 1
        else:
            generate_tts(text, out, cfg)
            made += 1
            print(f"[narrate] scene {s['id']:>2}: narrated")
        if s.get("audio_path") != rel:
            s["audio_path"] = rel
            changed = True

    if changed:
        scenes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"[narrate] provider={provider} voice={voice} — {made} narrated, {cached} cached "
          f"({len(scenes)} scenes) -> {audio_dir}")
    return audio_dir
