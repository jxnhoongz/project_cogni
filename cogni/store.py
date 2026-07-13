"""Thin scenes.json / audio helpers for the web UI.

Keeps the UI dumb: read scenes into an editable table, write narration + animate
edits back, save/override a scene's audio, report status, build a preview
storyboard. All real work stays in the stage functions.
"""

from __future__ import annotations

import base64
import html
import io
import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image

from .audio import _find_audio
from .config import active_project, load_config, project_root, resolve_path

TABLE_HEADERS = ["ID", "Narration (edit me)", "Animate"]


def load_scenes(cfg: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if active_project() is None:
        return None
    cfg = cfg or load_config()
    p = resolve_path(cfg, "scenes")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def scenes_table(cfg: dict[str, Any] | None = None) -> list[list[Any]]:
    """Rows for the UI grid: [id, narration, animate]."""
    doc = load_scenes(cfg)
    if not doc:
        return []
    return [
        [s["id"], s.get("narration") or s.get("narration_en", ""), bool(s.get("animate"))]
        for s in doc["scenes"]
    ]


def save_scene_edits(rows: list[list[Any]], cfg: dict[str, Any] | None = None) -> int:
    """Write the narration + animate columns from `rows` back into scenes.json."""
    cfg = cfg or load_config()
    p = resolve_path(cfg, "scenes")
    if not p.exists():
        raise FileNotFoundError("no scenes.json yet — generate a script first")
    doc = json.loads(p.read_text(encoding="utf-8"))
    by_id = {int(r[0]): r for r in rows if r and r[0] not in (None, "")}
    for s in doc["scenes"]:
        r = by_id.get(s["id"])
        if r:
            s["narration"] = str(r[1]).strip()
            s["animate"] = bool(r[2])
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(by_id)


def save_audio(scene_id: int, src_path: str, cfg: dict[str, Any] | None = None) -> Path:
    """Save/override a scene's audio as audio/scene_XXX.wav (transcoded via ffmpeg)."""
    cfg = cfg or load_config()
    audio_dir = resolve_path(cfg, "audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    stem = f"scene_{int(scene_id):03d}"
    for e in (".mp3", ".m4a", ".flac", ".ogg", ".aac"):
        alt = audio_dir / f"{stem}{e}"
        if alt.exists():
            alt.unlink()
    out = audio_dir / f"{stem}.wav"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src_path), "-ar", "44100", "-ac", "2", str(out)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"could not save audio: {proc.stderr.strip()[-300:]}")
    return out


def audio_status(cfg: dict[str, Any] | None = None) -> list[tuple[int, bool]]:
    """(scene_id, has_audio) for every scene."""
    cfg = cfg or load_config()
    doc = load_scenes(cfg)
    if not doc:
        return []
    audio_dir = resolve_path(cfg, "audio")
    return [(s["id"], _find_audio(audio_dir, s["id"]) is not None) for s in doc["scenes"]]


def scene_ids(cfg: dict[str, Any] | None = None) -> list[int]:
    doc = load_scenes(cfg)
    return [s["id"] for s in doc["scenes"]] if doc else []


def final_video_path(cfg: dict[str, Any] | None = None) -> str | None:
    """Path to the rendered final.mp4 for the active book, if it exists."""
    if active_project() is None:
        return None
    cfg = cfg or load_config()
    p = resolve_path(cfg, "output") / "final.mp4"
    return str(p) if p.exists() else None


def _b64_thumb(path: Path, width: int = 440) -> str:
    im = Image.open(path).convert("RGB")
    h = max(1, round(im.height * width / im.width))
    im = im.resize((width, h))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


_PREVIEW_CSS = """
<style>
.cg-title{font-weight:700;font-size:1.05rem;margin:4px 0 14px}
.cg-wrap{display:flex;flex-direction:column;gap:16px}
.cg-card{display:flex;gap:18px;border:1px solid rgba(128,128,128,.3);border-radius:12px;padding:14px;align-items:flex-start}
.cg-img{width:440px;max-width:42vw;border-radius:8px;flex:0 0 auto}
.cg-noimg{width:440px;max-width:42vw;height:200px;display:flex;align-items:center;justify-content:center;background:rgba(128,128,128,.12);border-radius:8px;opacity:.6;flex:0 0 auto}
.cg-body{flex:1;min-width:0}
.cg-head{font-weight:600;margin-bottom:10px}
.cg-narr{line-height:1.6}
.cg-badge{font-size:.72rem;padding:2px 9px;border-radius:999px;margin-left:6px;border:1px solid rgba(128,128,128,.4);white-space:nowrap}
.cg-badge.on{color:#2e9e4f;border-color:#2e9e4f}
.cg-badge.off{opacity:.55}
.cg-badge.anim{color:#c99a2e;border-color:#c99a2e}
</style>
"""


def preview_html(cfg: dict[str, Any] | None = None) -> str:
    """A storyboard: image + narration + caption + audio/animate status per scene."""
    doc = load_scenes(cfg)
    if not doc:
        return "<p style='opacity:.7'>No scenes yet — pick a book above, or upload one in tab 1 and generate a script.</p>"
    cfg = cfg or load_config()
    root = project_root(cfg)
    audio_dir = resolve_path(cfg, "audio")
    cards = []
    for s in doc["scenes"]:
        ip = s.get("image_path")
        p = (root / ip) if ip else None
        if p and p.exists():
            img = f'<img class="cg-img" src="{_b64_thumb(p)}"/>'
        else:
            img = '<div class="cg-noimg">no image yet</div>'
        has_audio = _find_audio(audio_dir, s["id"]) is not None
        badges = [f'<span class="cg-badge {"on" if has_audio else "off"}">{"🔊 narrated" if has_audio else "⬜ no audio"}</span>']
        if s.get("animate"):
            badges.append('<span class="cg-badge anim">🎬 animate</span>')
        cap = html.escape(s.get("on_screen_text") or "")
        cards.append(
            f'<div class="cg-card">{img}<div class="cg-body">'
            f'<div class="cg-head">Scene {s["id"]}{" · " + cap if cap else ""} {"".join(badges)}</div>'
            f'<div class="cg-narr">{html.escape(s.get("narration") or s.get("narration_en", ""))}</div>'
            f"</div></div>"
        )
    title = html.escape(doc.get("project_title", ""))
    return (
        _PREVIEW_CSS
        + f'<div class="cg-title">{title} — {len(doc["scenes"])} scenes</div>'
        + '<div class="cg-wrap">' + "".join(cards) + "</div>"
    )


def scene_images(cfg: dict[str, Any] | None = None) -> list[tuple[str, str]]:
    """(image_path, caption) for scenes whose image exists — for a UI gallery."""
    cfg = cfg or load_config()
    doc = load_scenes(cfg)
    if not doc:
        return []
    root = project_root(cfg)
    out: list[tuple[str, str]] = []
    for s in doc["scenes"]:
        ip = s.get("image_path")
        p = (root / ip) if ip else None
        if p and p.exists():
            out.append((str(p), f"Scene {s['id']}: {s.get('on_screen_text') or ''}".strip()))
    return out
