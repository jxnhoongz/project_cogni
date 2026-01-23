---
name: youtube-analytics-puller
description: Fetches YouTube performance metrics via Analytics API. Pulls views, CTR, avg view %, likes, comments. Calculates success scores, flags underperformers. Use daily (24h after upload), weekly, or when asking "how is [video] performing?"
---

# YouTube Analytics Puller

Fetches and analyzes video performance metrics.

## Fetch Metrics

```bash
python scripts/fetch_youtube_metrics.py --video-id dQw4w9WgXcQ --period 7d
```

Output:
```json
{
  "video_id": "dQw4w9WgXcQ",
  "metrics": {
    "views": 1247,
    "ctr": 4.2,
    "avg_view_duration_pct": 68,
    "likes": 143,
    "comments": 12
  },
  "success_score": 0.72,
  "status": "performing"
}
```

## Success Score

`score = CTR × 0.4 + avg_view_pct × 0.6`

| Score | Status |
|-------|--------|
| >0.7 | Performing |
| 0.5-0.7 | Average |
| <0.5 | Underperforming |

## Flag Underperformers

```bash
python scripts/flag_underperformers.py --threshold 0.5
```

Identifies videos with CTR <2% or avg view <30%.

## Export CSV

```bash
python scripts/export_metrics_csv.py --period 7d --output metrics.csv
```

Weekly export for trend analysis.

## Metrics Schedule

- **24h after upload**: First performance check
- **7d after upload**: Full metrics pull
- **Weekly**: All videos summary