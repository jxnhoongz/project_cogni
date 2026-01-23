---
name: metadata-optimizer
description: Generates optimized YouTube titles, descriptions, tags for maximum CTR. Creates A/B test variants, applies SEO principles. Use after script generation, when asking "optimize title", or before upload.
---

# Metadata Optimizer

Generates CTR-optimized titles, descriptions, and tags.

## Generate Title Variants

```bash
python scripts/generate_titles.py --script script.json --count 3
```

Output:
```json
{
  "titles": [
    "Stop Chasing Goals. Fix Your Identity.",
    "Why Goals Don't Work (And What Does)",
    "The Identity Shift That Changes Everything"
  ]
}
```

## Title Guidelines

- Problem + payoff structure
- Under 60 characters
- No clickbait, but make a promise
- Front-load keywords

## Generate Description

```bash
python scripts/generate_description.py --script script.json
```

Template:
```
[1-sentence summary]

Key takeaways:
• Bullet 1
• Bullet 2

7-Day Challenge: [specific action]

📖 Book: [Title] by [Author]
🔗 [link]

---
Educational commentary. Support the author: [link]

#认知 #mindset #[tags]
```

## Hashtags

Mix of:
- Broad: #mindset #selfimprovement
- Niche: #atomichabits #认知
- Trending: Check topic-trend-researcher

## Output

```json
{
  "title_options": ["A", "B", "C"],
  "description": "...",
  "hashtags": ["#认知", "#habits"],
  "timestamps": [{"time": "0:00", "label": "Intro"}]
}
```