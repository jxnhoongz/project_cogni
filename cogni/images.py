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
import re
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


def _openrouter_image(prompt: str, out_path: Path, cfg: dict[str, Any],
                      ref: Path | None = None) -> None:
    """Generate one image via OpenRouter and write it to disk.

    Without `ref` this uses the plain /images endpoint. With `ref` (a character
    reference still) it goes through /chat/completions with the reference attached as
    an image part, which is how the Gemini image models keep a recurring character
    ON-MODEL. Text alone does not: an unanchored description let book #4 render its
    protagonist as a different person mid-video. The reference costs ~1.3k prompt
    tokens (~$0.0003) — negligible next to the ~$0.034 image itself.
    """
    key = require_env("OPENROUTER_API_KEY")
    img = cfg["image"]
    base = cfg["llm"]["base_url"].rstrip("/")  # https://openrouter.ai/api/v1
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    timeout = float(img.get("timeout_sec", 180))

    if ref is not None and ref.exists():
        b64 = base64.b64encode(ref.read_bytes()).decode()
        guided = (
            "The attached reference image defines the RECURRING CHARACTER. Whenever a "
            "person appears in the scene below, it is that exact same character: same "
            "face, skin tone, hair, build and signature clothing. Do not restyle them, "
            "do not age them, do not change their ethnicity. Compose a NEW scene:\n"
            f"{prompt}"
        )
        body: dict[str, Any] = {
            "model": img["model"],
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": guided},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ]}],
            "modalities": ["image", "text"],
        }
        try:
            r = httpx.post(f"{base}/chat/completions", headers=headers, json=body, timeout=timeout)
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenRouter image request failed: {e}") from e
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter image gen HTTP {r.status_code}: {r.text[:300]}")
        msg = ((r.json().get("choices") or [{}])[0].get("message") or {})
        images = msg.get("images") or []
        url = (images[0].get("image_url", {}) or {}).get("url", "") if images else ""
        if not url.startswith("data:"):
            raise RuntimeError(f"OpenRouter returned no image for a referenced scene: {r.text[:300]}")
        out_path.write_bytes(base64.b64decode(url.split(",", 1)[1]))
        return

    body = {"model": img["model"], "prompt": prompt}
    if img.get("aspect_ratio"):
        body["aspect_ratio"] = img["aspect_ratio"]
    try:
        r = httpx.post(f"{base}/images", headers=headers, json=body, timeout=timeout)
    except httpx.HTTPError as e:
        raise RuntimeError(f"OpenRouter image request failed: {e}") from e
    if r.status_code != 200:
        raise RuntimeError(f"OpenRouter image gen HTTP {r.status_code}: {r.text[:300]}")
    data = r.json().get("data")
    if not data or not data[0].get("b64_json"):
        raise RuntimeError(f"OpenRouter image gen returned no image: {r.text[:300]}")
    out_path.write_bytes(base64.b64decode(data[0]["b64_json"]))


def _comfy_image(prompt: str, out_path: Path, cfg: dict[str, Any]) -> None:
    """Generate one image via the local ComfyUI server (SDXL + faceted-low-poly LoRA).

    Free + local. Generates at the model's native res, then Lanczos-upscales to the
    video canvas (flat low-poly facets upscale cleanly). The style LoRA's trigger word
    is prepended; the STYLE token is already in `prompt`. Seed is derived from the scene
    filename so re-runs reproduce.
    """
    import hashlib
    import sys

    c = cfg["image"].get("comfy", {})
    scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from comfy_gen import generate  # local ComfyUI client

    trigger = c.get("trigger", "ral-polygon")
    full = prompt if trigger.lower() in prompt.lower() else f"{trigger}, {prompt}"
    seed = int(hashlib.sha1(out_path.stem.encode()).hexdigest()[:8], 16)
    gen_w, gen_h = int(c.get("gen_width", 1344)), int(c.get("gen_height", 768))

    tmp = out_path.with_name(out_path.stem + ".gen.png")
    generate(
        full, tmp, seed=seed, w=gen_w, h=gen_h,
        ckpt=c.get("ckpt", "dreamshaperXL_turbo.safetensors"),
        steps=int(c.get("steps", 7)), cfg=float(c.get("cfg", 2.0)),
        lora=c.get("lora", "polygon-style-sdxl.safetensors"),
        lora_str=float(c.get("lora_strength", 0.9)),
        timeout_s=int(c.get("timeout_sec", 300)),
    )
    # Upscale to the delivery size (default 2560x1440 = zoom headroom for Ken Burns,
    # matching the channel's other images). Lanczos keeps flat low-poly facets crisp.
    ow, oh = int(c.get("out_width", 2560)), int(c.get("out_height", 1440))
    with Image.open(tmp) as im:
        im.convert("RGB").resize((ow, oh), Image.LANCZOS).save(out_path, "PNG")
    tmp.unlink(missing_ok=True)


def generate_image(prompt: str, out_path: Path, cfg: dict[str, Any], label: str = "",
                   ref: Path | None = None) -> None:
    """Generate one image for `prompt` at out_path, per config image.provider.

    `ref` is an optional recurring-character reference still (openrouter only).
    """
    provider = cfg["image"]["provider"]
    if provider == "mock":
        _mock_image(prompt, out_path, _canvas_size(cfg), label or out_path.stem)
    elif provider == "openrouter":
        _openrouter_image(prompt, out_path, cfg, ref=ref)
    elif provider == "comfy":
        _comfy_image(prompt, out_path, cfg)
    else:
        raise RuntimeError(
            f"unknown image provider '{provider}' (use 'comfy', 'openrouter', or 'mock')"
        )


# Does this shot contain a person? Only those need the character reference — sending a
# face reference into a pure object/landscape shot just biases it toward inserting one.
_PERSON_RE = re.compile(
    r"\b(he|him|his|she|her|they|man|woman|guy|person|people|crowd|figure|face|hand|hands|"
    r"shoulder|silhouette|protagonist|kid|child|boy|girl)\b", re.I)


def _shot_has_person(prompt: str, character: dict[str, Any] | None) -> bool:
    name = ((character or {}).get("name") or "").strip()
    first = name.split()[0] if name else ""
    if first and re.search(rf"\b{re.escape(first)}\b", prompt, re.I):
        return True
    return bool(_PERSON_RE.search(prompt))


def _ensure_character_ref(cfg: dict[str, Any], character: dict[str, Any] | None,
                          images_dir: Path, style: str) -> Path | None:
    """One canonical portrait of the recurring character, generated once and reused.

    This is the anchor that keeps the protagonist on-model across a whole book. Cached:
    delete `_character_ref.png` to re-roll the character's look.
    """
    desc = ((character or {}).get("description") or "").strip()
    if not desc or cfg["image"]["provider"] != "openrouter":
        return None
    ref = images_dir / "_character_ref.png"
    if ref.exists():
        return ref
    name = ((character or {}).get("name") or "the protagonist").strip()
    prompt = (
        f"Character reference sheet: a single clear head-and-shoulders portrait of {name}, "
        f"facing the camera, neutral expression, even lighting, plain uncluttered background. "
        f"{desc} {style}"
    ).strip()
    print(f"[images] building character reference for {name} -> {ref.name}")
    _openrouter_image(prompt, ref, cfg)          # no ref yet — this IS the reference
    return ref


def _image_prompt(base: str, character: dict[str, Any] | None, style: str) -> str:
    """Beat prompt + optional recurring-character clause + STYLE token."""
    parts = [base.strip()]
    desc = ((character or {}).get("description") or "").strip()
    if desc:
        parts.append(f"Recurring character, only if a person appears in this shot: {desc}.")
    if style.strip():
        parts.append(style.strip())
    return " ".join(p for p in parts if p).strip()


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
    character = doc.get("character")

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
    char_ref = _ensure_character_ref(cfg, character, images_dir, style)
    made = cached = referenced = 0
    changed = False
    for s in scenes:
        # One still per scene. NB: we deliberately do NOT generate an end keyframe for
        # animate scenes — the cogni-animate skill drives motion from the single start
        # still plus a camera-move prompt (two near-identical keyframes froze the clips),
        # so end stills were pure waste.
        start_out = images_dir / f"scene_{s['id']:03d}.png"
        if start_out.exists() and not force:
            cached += 1
        else:
            base = (s.get("start_image_prompt") or s.get("image_prompt") or "").strip()
            if not base:
                raise RuntimeError(
                    f"scene {s['id']} has no image prompt — run `script` (and `visuals`)."
                )
            full = _image_prompt(base, character, style)
            ref = char_ref if (char_ref and _shot_has_person(base, character)) else None
            generate_image(full, start_out, cfg, label=f"Scene {s['id']}", ref=ref)
            made += 1
            referenced += 1 if ref else 0
        start_rel = str(start_out.relative_to(root_parent))
        if s.get("image_path") != start_rel:
            s["image_path"] = start_rel
            changed = True
        if s.get("end_image_path") is not None:
            s["end_image_path"] = None      # drop stale references to retired end stills
            changed = True

    if changed:
        scenes_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"[images] provider={provider} — {made} generated ({referenced} character-locked), "
          f"{cached} cached ({len(scenes)} scenes) -> {images_dir}")
    return images_dir
