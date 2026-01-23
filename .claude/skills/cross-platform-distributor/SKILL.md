---
name: cross-platform-distributor
description: Shares content to Twitter, Reddit, LinkedIn after YouTube upload. Extracts teasers, respects platform rules. Use after YouTube upload, when saying "share on Twitter", or in distribution pipeline (Phase 2+).
---

# Cross Platform Distributor

Distributes content across social platforms after YouTube publish.

## Supported Platforms

| Platform | Content | Rules |
|----------|---------|-------|
| Twitter/X | Teaser + link | Max 280 chars |
| Reddit | Title + link | Respect subreddit rules |
| LinkedIn | Professional frame | Longer format OK |

## Post to Twitter

```bash
python scripts/post_to_twitter.py \
  --video-url "https://youtube.com/watch?v=xxx" \
  --teaser "Stop chasing goals. Fix your identity first." \
  --hashtags "#mindset #认知"
```

## Post to Reddit

```bash
python scripts/post_to_reddit.py \
  --video-url "https://youtube.com/watch?v=xxx" \
  --title "Key insight from Atomic Habits" \
  --subreddit "productivity"
```

## Platform Guidelines

**Twitter:** Lead with hook, 2-3 hashtags, link at end
**Reddit:** Match subreddit tone, don't spam
**LinkedIn:** Professional framing, tag topics

## Output

```json
{
  "platform": "twitter",
  "post_id": "123456789",
  "url": "https://twitter.com/...",
  "posted_at": "2025-10-12T16:00:00Z"
}
```