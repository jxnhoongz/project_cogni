---
name: pivot-advisor
description: Detects when channel strategy needs adjustment. Analyzes 4-week rolling metrics, identifies failure patterns (declining CTR, low retention, subscriber stall), suggests pivots. Use weekly for retrospective, when growth stalls, or when asking "what should I change?"
---

# Pivot Advisor

Detects stagnation and recommends strategic adjustments.

## Analyze Pivot Need

```bash
python scripts/analyze_pivot_need.py --weeks 4
```

Output:
```json
{
  "issue_detected": true,
  "patterns": ["declining_ctr", "subscriber_stall"],
  "metrics": {
    "ctr_trend": -0.22,
    "view_trend": -0.16,
    "subscriber_growth": 126
  },
  "root_cause_hypothesis": "Hook patterns becoming stale",
  "recommended_actions": [
    "Test new hook styles",
    "Review thumbnail contrast"
  ],
  "urgency": "medium"
}
```

## Failure Patterns

| Pattern | Trigger | Typical Cause |
|---------|---------|---------------|
| `declining_ctr` | >20% CTR drop over 4 weeks | Stale hooks/thumbnails |
| `low_retention` | Avg view <30% | Script pacing, filler |
| `subscriber_stall` | <40 subs in 4 weeks | Content-audience mismatch |
| `declining_views` | >30% views drop | Posting inconsistency |

## Urgency Levels

- **High**: 3+ patterns detected → immediate action
- **Medium**: 2 patterns → review within week
- **Low**: 1 pattern → monitor closely
- **None**: Channel performing well

## Pivot Actions by Pattern

### Declining CTR
1. Review hook_style A/B test results
2. Test contrarian vs question hooks
3. Audit thumbnail text/contrast

### Low Retention
1. Tighten scripts - target <15% filler
2. Front-load value in first 30s
3. Increase pacing, reduce pauses

### Subscriber Stall
1. Survey audience preferences
2. Niche down (e.g., habits books only)
3. Review content-audience fit

### Declining Views
1. Check posting schedule consistency
2. Align topics with trend research
3. Review upload times

## Weekly Review Process

1. Run `analyze_pivot_need.py --weeks 4`
2. If `issue_detected: true`, review patterns
3. Cross-reference with A/B test results
4. Implement top recommendation
5. Monitor for 2 weeks before next pivot