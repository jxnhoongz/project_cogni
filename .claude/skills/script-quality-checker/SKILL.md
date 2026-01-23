---
name: script-quality-checker
description: Validates scripts before TTS conversion. Checks word count, hook strength, generic phrases, concrete examples, action steps, readability. Use after every script generation, before TTS, or when asking "is this script good enough?"
---

# Script Quality Checker

Auto-validates scripts against quality bar before production.

## Quality Checks

### Shorts (130-260 words)

| Check | Pass Criteria |
|-------|---------------|
| Word count | 130-260 words |
| Hook length | ≤12 words |
| Generic phrases | None detected |
| Concrete example | Present |
| Action step | Specific (not vague) |

### Midform (8000-10000 words)

| Check | Pass Criteria |
|-------|---------------|
| Word count | 8000-10000 words |
| Chapter count | 4-5 chapters |
| Has 7-day experiment | Present |

## Run Validation

```bash
python scripts/validate_script.py --script script.json --format shorts
```

Output:
```json
{
  "passed": true,
  "checks": {
    "word_count": {"passed": true, "value": 185},
    "hook_length": {"passed": true, "value": 9},
    "generic_phrases": {"passed": true, "found": []}
  },
  "action": "proceed"
}
```

## Generic Phrases to Detect

- "In today's video"
- "Let's dive in"
- "Hey guys"
- "Welcome back"

## Failure Actions

- `word_count` fail → Regenerate
- `hook_length` fail → Rewrite hook only
- `generic_phrases` fail → Replace phrases
