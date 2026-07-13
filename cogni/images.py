"""Stage 4: images — one still per scene into images/scene_XXX.png.

`generate_image()` is a pluggable provider. Provider "mock" writes a free
placeholder PNG (no API, no credits) so `assemble` has something to work with;
a real provider (OpenRouter image-gen) gets wired in later. The single STYLE
token from docs/STYLE.md is appended to EVERY prompt here — change the look in
one place.
"""

from __future__ import annotations

import base64
import json
import textwrap
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from .config import load_config, load_style_token, project_root, require_env, resolve_path
from .review import review_gate


def _canvas_size(cfg: dict[str, Any]) -> tuple[int, int]:
    v = cfg["video"]
    return int(v["width"]), int(v["height"])


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _mock_image(prompt: str, out_path: Path, size: tuple[int, int], label: str) -> None:
    """Draw a placeholder: dark card + the (style-appended) prompt text + label."""
    w, h = size
    img = Image.new("RGB", size, (24, 26, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, w - 20, h - 20], outline=(80, 84, 92), width=3)

    draw.text((48, 40), label, fill=(210, 180, 120), font=_font(46))
    body = _font(30)
    y = 130
    for line in textwrap.wrap(prompt, width=70):
        draw.text((48, y), line, fill=(220, 222, 226), font=body)
        y += 40
        if y > h - 80:
            draw.text((48, y), "…", fill=(220, 222, 226), font=body)
            break
    draw.text((48, h - 60), "[MOCK IMAGE — provider not wired yet]", fill=(120, 124, 132), font=_font(26))
    img.save(out_path, "PNG")


def _openrouter_image(prompt: str, out_path: Path, cfg: dict[str, Any]) -> None:
    """Generate one image via OpenRouter's /images endpoint and write it to disk."""
    key = require_env("OPENROUTER_API_KEY")
    img = cfg["image"]
    base = cfg["llm"]["base_url"].rstrip("/")  # https://openrouter.ai/api/v1
    body: dict[str, Any] = {"model": img["model"], "prompt": prompt}
    if img.get("aspect_ratio"):
        body["aspect_ratio"] = img["aspect_ratio"]
    try:
        r = httpx.post(
            f"{base}/images",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=body, timeout=float(img.get("timeout_sec", 180)),
        )
    except httpx.HTTPError as e:
        raise RuntimeError(f"OpenRouter image request failed: {e}") from e
    if r.status_code != 200:
        raise RuntimeError(f"OpenRouter image gen HTTP {r.status_code}: {r.text[:300]}")
    data = r.json().get("data")
    if not data or not data[0].get("b64_json"):
        raise RuntimeError(f"OpenRouter image gen returned no image: {r.text[:300]}")
    out_path.write_bytes(base64.b64decode(data[0]["b64_json"]))


def generate_image(prompt: str, out_path: Path, cfg: dict[str, Any], label: str = "") -> None:
    """Generate one image for `prompt` at out_path, per config image.provider."""
    provider = cfg["image"]["provider"]
    if provider == "mock":
        _mock_image(prompt, out_path, _canvas_size(cfg), label or out_path.stem)
    elif provider == "openrouter":
        _openrouter_image(prompt, out_path, cfg)
    else:
        raise RuntimeError(
            f"unknown image provider '{provider}' (use 'openrouter' or 'mock')"
        )


def images(
    *, force: bool = False, skip_review: bool = False, cfg: dict[str, Any] | None = None
) -> Path:
    """Generate a still for every scene in scenes.json (cached). Returns images dir.

    Uses each scene's start_image_prompt (the `visuals` keyframe), falling back to
    the older image_prompt. If any scene has visual prompts, the `review` gate must
    pass first (override with skip_review) — the safety net before spending credits.
    """
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(
            f"{scenes_path} not found — run `script` first to create it."
        )
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    if not skip_review:
        unreviewed, failing = review_gate(scenes)
        if unreviewed or failing:
            parts = []
            if unreviewed:
                parts.append(f"not reviewed yet: {unreviewed} (run `review`)")
            if failing:
                parts.append(f"failing review: {failing} (fix prompts or re-run `visuals`)")
            raise RuntimeError(
                "review gate — refusing to spend image credits. "
                + "; ".join(parts)
                + ". Override with --skip-review."
            )

    images_dir = resolve_path(cfg, "images")
    images_dir.mkdir(parents=True, exist_ok=True)
    style = load_style_token()
    root_parent = project_root(cfg)  # project root, for relative paths

    provider = cfg["image"]["provider"]
    made = cached = 0
    changed = False
    for s in scenes:
        # Start keyframe — every scene gets one.
        start_out = images_dir / f"scene_{s['id']:03d}.png"
        if start_out.exists() and not force:
            cached += 1
        else:
            base = (s.get("start_image_prompt") or s.get("image_prompt") or "").strip()
            if not base:
                raise RuntimeError(
                    f"scene {s['id']} has no image prompt — run `script` (and `visuals`)."
                )
            generate_image(f"{base} {style}".strip(), start_out, cfg, label=f"Scene {s['id']}")
            made += 1
        start_rel = str(start_out.relative_to(root_parent))
        if s.get("image_path") != start_rel:
            s["image_path"] = start_rel
            changed = True

        # End keyframe — only for scenes flagged animate=true (the second frame of
        # the start->end hero clip). Non-animate scenes stay single stills.
        if s.get("animate") and (s.get("end_image_prompt") or "").strip():
            end_out = images_dir / f"scene_{s['id']:03d}_end.png"
            if end_out.exists() and not force:
                cached += 1
            else:
                generate_image(
                    f"{s['end_image_prompt'].strip()} {style}".strip(),
                    end_out, cfg, label=f"Scene {s['id']} (end)",
                )
                made += 1
            end_rel = str(end_out.relative_to(root_parent))
            if s.get("end_image_path") != end_rel:
                s["end_image_path"] = end_rel
                changed = True
        elif s.get("end_image_path") is not None:
            # No longer animating (or no end prompt) — drop the stale end reference.
            s["end_image_path"] = None
            changed = True

    if changed:
        scenes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"[images] provider={provider} — {made} generated, {cached} cached ({len(scenes)} scenes) -> {images_dir}")
    return images_dir
