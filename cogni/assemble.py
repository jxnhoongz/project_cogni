"""Stage 5: assemble — scenes.json + images/audio -> output/final.mp4.

Per scene: measure the recorded audio's length (or use a silent placeholder in
preview mode); render the still with a subtle Ken Burns zoom (or use a hero clip
if clips/scene_XXX.mp4 exists); optionally burn the caption. Concatenate in id
order, mix low-volume background music from assets/audio/ if present, and export
1920x1080 H.264.

ffmpeg does the heavy lifting; each scene is built as its own clip first so the
pipeline is debuggable one scene at a time.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .config import load_config, project_root, resolve_path, resolve_shared

_MUSIC_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")


def _venc(cfg: dict[str, Any]) -> list[str]:
    """ffmpeg video-encoder args — Apple hardware (videotoolbox) or software (x264)."""
    v = cfg["video"]
    if v.get("encoder", "videotoolbox") == "videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-b:v", str(v.get("video_bitrate", "12M")),
                "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p"]


def _run(cmd: list[str], what: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()[-8:]
        raise RuntimeError(f"ffmpeg failed ({what}):\n" + "\n".join(tail))


def _probe_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError as e:
        raise RuntimeError(f"could not read duration of {path}: {proc.stderr[:200]}") from e


def _font(size: int) -> Any:
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _caption_png(text: str, size: tuple[int, int], out: Path) -> None:
    """Transparent overlay with the caption on a soft dark bar near the bottom."""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _font(52)
    lines = textwrap.wrap(text, width=46) or [text]
    line_h = 64
    block_h = line_h * len(lines)
    top = h - 150 - block_h
    pad = 28
    # backdrop bar
    draw.rectangle([0, top - pad, w, top + block_h + pad], fill=(15, 16, 20, 150))
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=font)
        draw.text(((w - tw) / 2, top + i * line_h), line, fill=(240, 236, 228, 255), font=font)
    img.save(out, "PNG")


def _scene_clip(
    scene: dict[str, Any],
    duration: float,
    audio: Path | None,
    tmp: Path,
    cfg: dict[str, Any],
) -> Path:
    """Build one scene's mp4 (video + audio) into tmp."""
    v = cfg["video"]
    w, h, fps = int(v["width"]), int(v["height"]), int(v["fps"])
    out = tmp / f"scene_{scene['id']:03d}.mp4"
    frames = max(1, round(duration * fps))

    # Synced subtitles from the narration's .srt (replaces the old caption bar).
    subs = None
    if bool(v.get("subtitles")) and audio is not None:
        srt_src = audio.with_suffix(".srt")
        if srt_src.exists():
            subs = tmp / f"sub_{scene['id']:03d}.srt"
            shutil.copyfile(srt_src, subs)
    burn = (
        subs is None
        and bool(v.get("burn_captions"))
        and bool(scene.get("on_screen_text"))
    )

    inputs: list[str] = []
    clip_path = scene.get("clip_path")
    if clip_path and (project_root(cfg) / clip_path).exists():
        # Hero clip: scale/crop to frame, trim/loop to duration.
        src = project_root(cfg) / clip_path
        inputs += ["-stream_loop", "-1", "-i", str(src)]
        vchain = f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},format=yuv420p"
    else:
        # Still + Ken Burns zoom.
        img = project_root(cfg) / scene["image_path"]
        zmax = float(v.get("ken_burns_zoom", 1.08))
        step = (zmax - 1.0) / frames
        inputs += ["-loop", "1", "-framerate", str(fps), "-i", str(img)]
        vchain = (
            f"[0:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
            f"zoompan=z='min(zoom+{step:.6f},{zmax})':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},format=yuv420p"
        )

    if subs is not None:
        style = ("FontName=DejaVu Sans,FontSize=15,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H90000000,BorderStyle=1,Outline=2,Shadow=0,"
                 "Alignment=2,MarginV=52")
        vchain += f",subtitles='{subs}':force_style='{style}'"

    # Audio input (index 1).
    if audio is not None:
        inputs += ["-i", str(audio)]
    else:
        inputs += ["-f", "lavfi", "-t", f"{duration}",
                   "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    # Caption overlay input (index 2) if needed.
    filtergraph = f"{vchain}[v]"
    vmap = "[v]"
    if burn:
        cap = tmp / f"cap_{scene['id']:03d}.png"
        _caption_png(scene["on_screen_text"], (w, h), cap)
        inputs += ["-loop", "1", "-i", str(cap)]
        filtergraph = f"{vchain}[bg];[bg][2:v]overlay=0:0:format=auto,format=yuv420p[v]"

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filtergraph,
        "-map", vmap, "-map", "1:a",
        "-t", f"{duration}",
        *_venc(cfg), "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        str(out),
    ]
    _run(cmd, f"scene {scene['id']}")
    return out


def _find_music(cfg: dict[str, Any]) -> Path | None:
    music_dir = resolve_shared(cfg, "music")
    if not music_dir.exists():
        return None
    for p in sorted(music_dir.iterdir()):
        if p.suffix.lower() in _MUSIC_EXTS:
            return p
    return None


def _concat(clips: list[Path], out: Path, cfg: dict[str, Any]) -> None:
    listfile = out.parent / "concat_list.txt"
    listfile.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    _run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         *_venc(cfg), "-c:a", "aac", "-b:a", "192k", str(out)],
        "concat",
    )


def _mix_music(video_in: Path, music: Path, out: Path, cfg: dict[str, Any]) -> None:
    vol = float(cfg["video"].get("music_volume", 0.08))
    _run(
        ["ffmpeg", "-y", "-i", str(video_in), "-stream_loop", "-1", "-i", str(music),
         "-filter_complex",
         f"[1:a]volume={vol}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", str(out)],
        "music mix",
    )


def assemble(*, force: bool = False, cfg: dict[str, Any] | None = None) -> Path:
    """Render output/final.mp4 from scenes.json + images (+ audio if recorded)."""
    cfg = cfg or load_config()
    scenes_path = resolve_path(cfg, "scenes")
    if not scenes_path.exists():
        raise FileNotFoundError(f"{scenes_path} not found — run `script` first.")
    doc = json.loads(scenes_path.read_text(encoding="utf-8"))
    scenes = doc.get("scenes", [])
    if not scenes:
        raise RuntimeError(f"{scenes_path} has no scenes.")

    out_dir = resolve_path(cfg, "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / "final.mp4"
    if final.exists() and not force:
        print(f"[assemble] cached — {final} exists (use --force to re-render)")
        return final

    root_parent = project_root(cfg)
    audio_dir = resolve_path(cfg, "audio")
    preview_sec = float(cfg["video"].get("preview_scene_sec", 4.0))

    # Validate images exist.
    missing_img = [s["id"] for s in scenes if not s.get("image_path")
                   or not (root_parent / s["image_path"]).exists()]
    if missing_img:
        raise RuntimeError(f"missing images for scene(s) {missing_img} — run `images` first.")

    placeholders = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        clips = []
        for s in scenes:
            audio = None
            ap = s.get("audio_path")
            if ap and (root_parent / ap).exists():
                audio = root_parent / ap
                duration = _probe_duration(audio)
            else:
                # try to find a recording not yet recorded into scenes.json
                found = next(
                    (audio_dir / f"scene_{s['id']:03d}{e}" for e in
                     (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac")
                     if (audio_dir / f"scene_{s['id']:03d}{e}").exists()),
                    None,
                )
                if found:
                    audio = found
                    duration = _probe_duration(found)
                else:
                    duration = preview_sec
                    placeholders += 1
            print(f"[assemble] scene {s['id']:>2}: {duration:5.1f}s "
                  f"{'(voice)' if audio else '(silent placeholder)'}")
            clips.append(_scene_clip(s, duration, audio, tmp, cfg))

        concat = tmp / "concat.mp4"
        _concat(clips, concat, cfg)

        music = _find_music(cfg)
        if music:
            print(f"[assemble] mixing music: {music.name}")
            _mix_music(concat, music, final, cfg)
        else:
            concat.replace(final)

    mode = f"PREVIEW ({placeholders} silent placeholder scene(s))" if placeholders else "full (all voiced)"
    print(f"[assemble] wrote {final} — {len(scenes)} scenes, {mode}.")
    return final
