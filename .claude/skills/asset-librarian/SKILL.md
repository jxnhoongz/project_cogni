---
name: asset-librarian
description: Generates AI images matching voiceover content in Da Vinci oil painting style. Uses DALL-E 3 API. Use when generating visuals for scripts, creating scene images, or preparing assets for video rendering.
---

# Asset Librarian

Generates AI images in Da Vinci oil painting style to match voiceover content.

## Generate Image

```bash
python scripts/generate_image.py \
  --text "The power of compound habits transforms your daily routine" \
  --output scene_01.png
```

Output:
```json
{
  "id": "img_20251012_001",
  "prompt": "A person writing in a journal at dawn... Da Vinci oil painting style...",
  "local_path": "cognilab/assets/generated/scene_01.png",
  "created_at": "2024-10-12T08:30:00Z"
}
```

## Batch Generate from Script

```bash
python scripts/generate_from_script.py \
  --script script.json \
  --output-dir cognilab/assets/generated/
```

Generates one image per scene/segment in the script.

## Style

All images use consistent prompt suffix:
```
Renaissance oil painting style, Leonardo da Vinci technique,
sfumato shading, muted earth tones, dramatic chiaroscuro lighting,
museum quality fine art, 16th century Italian master painting
```

## Image Specs

- Resolution: 1024x1792 (portrait for shorts) or 1792x1024 (landscape for midform)
- Format: PNG
- API: OpenAI DALL-E 3

## Environment

Requires `OPENAI_API_KEY` environment variable.

## Cost

~$0.04-0.08 per image (DALL-E 3 standard quality)