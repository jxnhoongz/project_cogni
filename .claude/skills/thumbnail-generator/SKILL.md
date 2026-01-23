---
name: thumbnail-generator
description: Creates eye-catching thumbnails for midform videos. Extracts 3-5 word hooks, combines book cover with bold text overlay. Uses Canva API or ffmpeg+ImageMagick. Use after midform script finalized, when saying "generate thumbnail", or in midform pipeline.
---

# Thumbnail Generator

Creates high-contrast thumbnails for midform videos (1280x720).

## Template Structure

- Left 40%: Book cover image
- Right 60%: Bold text (3-5 word hook)
- High contrast for mobile visibility

## Generate Thumbnail

### Step 1: Extract Hook

```bash
python scripts/extract_thumbnail_hook.py --script midform.json
```

Output: `{"hook": "Fix Your Identity"}`

### Step 2: Generate Image

```bash
bash scripts/generate_thumbnail_ffmpeg.sh \
  --cover book_cover.jpg \
  --text "Fix Your Identity" \
  --output M_20251015_thumb.jpg
```

## Specifications

- Resolution: 1280x720
- Format: JPEG (optimized)
- Text: Sans-serif, 120pt, white on dark
- Max text: 5 words

## Output

```json
{
  "thumbnail_file": "M_20251015_thumb.jpg",
  "hook_text": "Fix Your Identity",
  "method": "ffmpeg"
}
```