---
name: copyright-compliance-checker
description: Ensures fair use compliance for book summary videos. Detects long quotes (>50 words), validates transformative commentary, checks attribution. Use after script generation, before publish, or when asking "is this safe to publish?"
---

# Copyright Compliance Checker

Validates scripts for fair use compliance.

## Fair Use Four-Factor Test

1. **Purpose**: Educational/transformative ✓
2. **Nature**: Published work ✓
3. **Amount**: Small portion ✓
4. **Market effect**: Doesn't replace book ✓

## Compliance Checks

| Check | Criteria | Risk |
|-------|----------|------|
| Quote length | Each <50 words | High |
| Total quoted | <300 words | Medium |
| Attribution | Book/author mentioned | High |
| Transformative | Has analysis | High |

## Run Check

```bash
python scripts/check_compliance.py --script script.json
```

Output:
```json
{
  "compliant": true,
  "risk_level": "low",
  "checks": {
    "long_quotes": {"passed": true, "longest": 42},
    "has_attribution": {"passed": true}
  }
}
```

## Required Disclaimer

Every description must include:
```
This is educational commentary. To support the author, buy the book: [link]
```

## If Compliance Fails

1. Shorten quotes to <50 words
2. Add more original analysis
3. Ensure attribution
4. Re-run check
