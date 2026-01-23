---
name: topic-trend-researcher
description: Researches trending topics and books in self-improvement niche. Analyzes Google Trends, YouTube trends, Reddit mentions. Matches trends to catalog books, suggests new additions. Use weekly for trend checks, when asking "what's trending?", or when planning content strategy.
---

# Topic Trend Researcher

Finds trending topics in habits, productivity, finance, mindset niches.

## Research Sources

- Google Trends - Search volume, rising queries
- YouTube - Top performing book summary videos
- Reddit - r/productivity, r/selfimprovement mentions

## Run Trend Check

```bash
python scripts/research_trends.py --niche "self-improvement"
```

Output:
```json
{
  "trends": [
    {"topic": "dopamine detox", "growth_rate": 0.45, "related_books": ["bk_0001"], "opportunity_score": 0.82}
  ],
  "catalog_matches": [{"book_id": "bk_0002", "title": "Deep Work", "trend_relevance": 0.89}],
  "new_book_recommendations": [{"title": "Slow Productivity", "trend_score": 0.78}]
}
```

## Opportunity Score

`growth_rate × 0.4 + search_volume × 0.3 + catalog_coverage × 0.3`

## Weekly Workflow

1. Run `research_trends.py` every Monday
2. Review top 5 opportunities
3. Add high-potential books to catalog
4. Prioritize trending topics in content calendar
