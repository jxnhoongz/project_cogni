---
name: youtube-uploader
description: Uploads videos to YouTube via Data API v3 with optimized metadata. Handles title, description, tags, chapters, thumbnails, visibility. Use after render completes, when saying "upload [video_id]", or in publish pipeline.
---

# YouTube Uploader

Uploads videos to YouTube with proper metadata via API.

## Upload Video

```bash
python scripts/upload_to_youtube.py \
  --video render.mp4 \
  --title "Stop Chasing Goals" \
  --description description.txt \
  --tags "认知,habits,mindset" \
  --visibility public \
  --thumbnail thumb.jpg
```

## Required Setup

1. Create Google Cloud project
2. Enable YouTube Data API v3
3. Create OAuth credentials
4. Save as `credentials.json`

## Output

```json
{
  "video_id": "dQw4w9WgXcQ",
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "uploaded_at": "2025-10-12T15:30:00Z",
  "visibility": "public"
}
```

## Chapters (Midform)

For midform videos, include timestamps in description:
```
0:00 Intro
2:15 Chapter 1 - Identity
8:42 Chapter 2 - Environment
```

## Retry Logic

- 3 retries with exponential backoff
- Falls back to manual queue on persistent failure
- Logs all attempts to job file

## Post-Upload

Updates job file with:
- YouTube video ID
- Upload timestamp
- Public URL