---
name: dedup-validator
description: Prevents duplicate content by checking topic/angle collision before script generation. Enforces cooldown rules (21-day shorts, 60-day midform, 14-day same angle). Use before every script generation, when validating proposed topics, or when asking "have we done this before?"
---

# Dedup Validator

Prevents duplicate or repetitive content by checking against recent coverage history.

## Cooldown Rules

| Rule | Cooldown | Description |
|------|----------|-------------|
| Shorts topic | 21 days | Same core topic cannot repeat within 21 days |
| Midform book | 60 days | Same book midform cannot repeat within 60 days |
| Same angle | 14 days | Exact angle (any book) cannot repeat within 14 days |

## Usage

### Check Before Script Generation

```bash
python scripts/check_collision.py --topic "identity-based habits" --book-id bk_0001 --format shorts
```

Output:
```json
{
  "ok": true,
  "reason": "No collision detected"
}
```

Or if collision:
```json
{
  "ok": false,
  "reason": "Angle 'identity-based habits' used 8 days ago (S_20251005_01)",
  "days_since": 8,
  "rule_violated": "14-day angle cooldown",
  "alternatives": [
    {"book_id": "bk_0001", "angle": "environment design", "freshness": 0.92},
    {"book_id": "bk_0003", "angle": "asset vs liability mindset", "freshness": 0.88}
  ]
}
```

### Generate Alternatives

```bash
python scripts/generate_alternatives.py --original-topic "identity habits" --count 3
```

Returns 3 fresh alternatives from catalog.

## Validation Flow

```
Proposed Topic
    ↓
Check exact angle match (14-day rule)
    ↓ collision?
Check semantic similarity (>0.85 = too similar)
    ↓ collision?
Check book-specific rules (21/60 day)
    ↓ collision?
PASS → Proceed to script generation
```

## Integration

Always run dedup check BEFORE calling shorts-script-generator or midform-script-generator. If collision detected, either:
1. Use suggested alternative
2. Ask user to pick different topic
3. Override with explicit confirmation (rare)
