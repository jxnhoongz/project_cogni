---
name: video-renderer
description: Renders final videos by combining background, voiceover, and captions using ffmpeg. Supports shorts (1080x1920) and midform (1920x1080). Use after TTS completes, when saying "render [video_id]", or in production pipeline.
---

# Video Renderer

Combines assets into final video using ffmpeg.

## Output Specs

| Format | Resolution | FPS | Codec | Audio |
|--------|------------|-----|-------|-------|
| Shorts | 1080x1920 | 30 | H.264 CRF 19 | AAC 160k |
| Midform | 1920x1080 | 30 | H.264 CRF 19 | AAC 192k |

## Render Shorts

```bash
bash scripts/render_shorts.sh \
  --bg background.jpg \
  --audio vo.mp3 \
  --captions captions.ass \
  --output S_20251012_output.mp4
```

## Render Midform

```bash
bash scripts/render_midform.sh \
  --bg background.jpg \
  --audio vo.mp3 \
  --captions captions.srt \
  --output M_20251015_output.mp4
```

## Caption Generation

```bash
python scripts/generate_captions.py --audio vo.mp3 --output captions.ass
```

Uses Whisper or AssemblyAI for transcription.

## Rendering Pipeline

```
1. Fetch background (from asset-librarian)
2. Generate captions (Whisper transcription)
3. Render video (ffmpeg)
4. Validate output (check duration, corruption)
```

## Output

```json
{
  "video_file": "S_20251012_output.mp4",
  "resolution": "1080x1920",
  "fps": 30,
  "duration_sec": 95,
  "file_size_mb": 42,
  "codec": "h264"
}
```

## File Naming

- Shorts: `S_YYYYMMDD_titleSlug.mp4`
- Midform: `M_YYYYMMDD_titleSlug.mp4`