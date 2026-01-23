---
name: ab-test-coordinator
description: Runs hook/title experiments on videos. Tags variants, tracks performance, calculates statistical significance, declares winners. Use every 10th short (automated), when saying "run hook test", or for weekly experiment review.
---

# A/B Test Coordinator

Manages experiments to optimize hooks, titles, and formats.

## Experiment Types

| Type | Variants | Min Sample |
|------|----------|------------|
| Hook style | Question vs Contrarian vs Story | 1000 views each |
| Title format | Short vs Long | 1000 views each |
| CTA | Follow vs Subscribe | 1000 views each |

## Tag Experiment

```bash
python scripts/tag_experiment.py \
  --video-id S_20251012_01 \
  --experiment hook_style \
  --variant contrarian
```

## Analyze Results

```bash
python scripts/analyze_ab_test.py --experiment hook_style
```

Output:
```json
{
  "experiment": "hook_style",
  "variants": {
    "question": {"ctr": 3.2, "views": 1250},
    "contrarian": {"ctr": 4.8, "views": 1180},
    "story": {"ctr": 3.9, "views": 1320}
  },
  "winner": "contrarian",
  "confidence": 0.92,
  "recommendation": "Use contrarian hooks more often"
}
```

## Statistical Significance

Uses chi-square test. Requires:
- Min 1000 views per variant
- 7 days of data
- >85% confidence to declare winner

## Update Prompts

After winner declared:
```bash
python scripts/update_prompt_library.py --winner contrarian
```

Incorporates winning pattern into prompt templates.

## Experiment Schedule

- Every 10th short = experiment video
- Review results weekly
- Rotate experiment types monthly