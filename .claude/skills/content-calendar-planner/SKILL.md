---
name: content-calendar-planner
description: Plans publishing schedule for 认知提升 YouTube channel. Generates balanced 7-day or 30-day calendars, manages shorts/midform ratio, ensures topic diversity, respects phase cadence targets. Use when planning week/month ahead, asking "what should we publish next?", or checking schedule balance.
---

# Content Calendar Planner

Plans and balances publishing schedule across formats and topics.

## Cadence Targets by Phase

| Phase | Shorts/week | Midform/week |
|-------|-------------|--------------|
| 1 (Weeks 1-4) | 3 | 0.5 (every 2 weeks) |
| 2 (Weeks 5-12) | 5 | 1 |
| 3 (Months 4-6) | 7 (daily) | 1-2 |

## Generate Calendar

```bash
python scripts/generate_calendar.py --days 7 --phase 1
```

Output:
```json
{
  "calendar": [
    {"day": "Mon", "date": "2025-10-14", "format": "shorts", "book_id": "bk_0001", "angle": "identity-based habits"},
    {"day": "Wed", "date": "2025-10-16", "format": "shorts", "book_id": "bk_0007", "angle": "wealth is what you don't see"}
  ],
  "stats": {"shorts": 3, "midform": 1, "unique_books": 4}
}
```

For low-energy weeks: `--energy low` reduces to 50% cadence.

## Diversity Rules

1. No same book 2 days in a row
2. Max 2 books from same category per week
3. Midform on weekends (higher engagement)
4. Alternate topic themes

## Check Diversity

```bash
python scripts/check_diversity.py --calendar calendar.json
```
