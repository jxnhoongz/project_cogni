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
VISUALS_HEADERS = ["ID", "Start image prompt", "End image prompt", "Motion (video) prompt"]


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


def visuals_table(cfg: dict[str, Any] | None = None) -> list[list[Any]]:
    """Rows for the visuals grid: [id, start_image_prompt, end_image_prompt, video_prompt]."""
    doc = load_scenes(cfg)
    if not doc:
        return []
    return [
        [
            s["id"],
            s.get("start_image_prompt", ""),
            s.get("end_image_prompt", ""),
            s.get("video_prompt", ""),
        ]
        for s in doc["scenes"]
    ]


def save_visual_edits(rows: list[list[Any]], cfg: dict[str, Any] | None = None) -> int:
    """Write the start/end/video prompt columns back into scenes.json.

    Editing a prompt invalidates that scene's prior review (it must pass again).
    """
    cfg = cfg or load_config()
    p = resolve_path(cfg, "scenes")
    if not p.exists():
        raise FileNotFoundError("no scenes.json yet — generate a script first")
    doc = json.loads(p.read_text(encoding="utf-8"))
    by_id = {int(r[0]): r for r in rows if r and r[0] not in (None, "")}
    for s in doc["scenes"]:
        r = by_id.get(s["id"])
        if not r:
            continue
        new = (str(r[1]).strip(), str(r[2]).strip(), str(r[3]).strip())
        old = (
            s.get("start_image_prompt", ""),
            s.get("end_image_prompt", ""),
            s.get("video_prompt", ""),
        )
        if new != old:
            s["start_image_prompt"], s["end_image_prompt"], s["video_prompt"] = new
            s["review"] = None  # prompts changed — stale review
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(by_id)


def review_status_md(cfg: dict[str, Any] | None = None) -> str:
    """Human-readable review state: pass/fail per scene + the specific issues."""
    doc = load_scenes(cfg)
    if not doc:
        return "_No scenes yet._"
    scenes = doc["scenes"]
    have_prompts = [s for s in scenes if (s.get("start_image_prompt") or "").strip()]
    if not have_prompts:
        return "_No visual prompts yet — click **Generate visual prompts** first._"
    reviewed = [s for s in have_prompts if isinstance(s.get("review"), dict)]
    if not reviewed:
        return (f"⬜ **Not reviewed.** {len(have_prompts)} scenes have prompts — "
                f"click **Run review** (free) to check them before generating images.")
    failing = [s for s in reviewed if not (s.get("review") or {}).get("ok")]
    lines = []
    if not failing and len(reviewed) == len(have_prompts):
        lines.append(f"✅ **All {len(reviewed)} scenes passed** — safe to generate images.")
    else:
        n_ok = len(reviewed) - len(failing)
        lines.append(f"⚠️ **{n_ok}/{len(have_prompts)} OK.** Fix the flagged scenes "
                     f"(edit prompts → Save → Run review), or generate anyway (skips gate).")
    for s in failing:
        issues = (s.get("review") or {}).get("issues", [])
        bullet = "; ".join(issues) if issues else "needs another look"
        lines.append(f"- **Scene {s['id']}** — {bullet}")
    return "\n\n".join(lines)


def narration_review_md(cfg: dict[str, Any] | None = None) -> str:
    """Human-readable narration-review state: strong vs flagged scenes + the notes."""
    doc = load_scenes(cfg)
    if not doc:
        return "_No scenes yet._"
    scenes = doc["scenes"]
    reviewed = [s for s in scenes if isinstance(s.get("narration_review"), dict)]
    if not reviewed:
        return "_Narration not reviewed yet — click **Review narration** (free)._"
    flagged = [s for s in reviewed if not (s.get("narration_review") or {}).get("ok")]
    lines = []
    if not flagged:
        lines.append(f"✅ **All {len(reviewed)} scenes read strong.**")
    else:
        n_ok = len(reviewed) - len(flagged)
        lines.append(f"⚠️ **{n_ok}/{len(scenes)} strong.** Revise the flagged scenes "
                     "(or edit by hand), then re-review.")
    for s in flagged:
        issues = (s.get("narration_review") or {}).get("issues", [])
        bullet = "; ".join(issues) if issues else "needs a sharper pass"
        lines.append(f"- **Scene {s['id']}** — {bullet}")
    return "\n\n".join(lines)


def fact_review_md(cfg: dict[str, Any] | None = None) -> str:
    """Human-readable fact-check state: clean vs flagged scenes + the grounding notes."""
    doc = load_scenes(cfg)
    if not doc:
        return "_No scenes yet._"
    scenes = doc["scenes"]
    reviewed = [s for s in scenes if isinstance(s.get("fact_review"), dict)]
    if not reviewed:
        return "_Not fact-checked yet — click **Fact-check vs book** (free)._"
    flagged = [s for s in reviewed if not (s.get("fact_review") or {}).get("ok")]
    lines = []
    if not flagged:
        lines.append(f"✅ **All {len(reviewed)} scenes grounded in the book.**")
    else:
        n_ok = len(reviewed) - len(flagged)
        lines.append(f"⚠️ **{n_ok}/{len(scenes)} grounded.** Fix the flagged scenes "
                     "(**Revise** grounds the rewrite in the book), then re-check.")
    for s in flagged:
        issues = (s.get("fact_review") or {}).get("issues", [])
        bullet = "; ".join(issues) if issues else "possible grounding issue"
        lines.append(f"- **Scene {s['id']}** — {bullet}")
    return "\n\n".join(lines)


def set_animate_all(flag: bool, cfg: dict[str, Any] | None = None) -> int:
    """Set animate = flag on every scene (the 'animate everything' toggle). Returns count."""
    cfg = cfg or load_config()
    p = resolve_path(cfg, "scenes")
    if not p.exists():
        raise FileNotFoundError("no scenes.json yet — generate a script first")
    doc = json.loads(p.read_text(encoding="utf-8"))
    for s in doc["scenes"]:
        s["animate"] = bool(flag)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(doc["scenes"])


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
.cg-badge.bad{color:#d1584f;border-color:#d1584f}
.cg-kf{display:flex;align-items:center;gap:8px;flex:0 0 auto}
.cg-kf .cg-img{width:210px;max-width:20vw}
.cg-arrow{opacity:.55;font-size:1.4rem}
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
            # For animate scenes, show the end keyframe beside the start (start -> end).
            ep = s.get("end_image_path")
            epath = (root / ep) if ep else None
            if s.get("animate") and epath and epath.exists():
                img = (
                    '<div class="cg-kf">'
                    f'{img}<span class="cg-arrow">→</span>'
                    f'<img class="cg-img" src="{_b64_thumb(epath)}"/>'
                    "</div>"
                )
        else:
            img = '<div class="cg-noimg">no image yet</div>'
        has_audio = _find_audio(audio_dir, s["id"]) is not None
        badges = [f'<span class="cg-badge {"on" if has_audio else "off"}">{"🔊 narrated" if has_audio else "⬜ no audio"}</span>']
        if s.get("animate"):
            badges.append('<span class="cg-badge anim">🎬 animate</span>')
        r = s.get("review")
        if isinstance(r, dict):
            if r.get("ok"):
                badges.append('<span class="cg-badge on">✓ review</span>')
            else:
                n = len(r.get("issues", []))
                badges.append(f'<span class="cg-badge bad">⚠ {n} issue{"" if n == 1 else "s"}</span>')
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
