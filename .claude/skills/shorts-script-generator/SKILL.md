---
name: shorts-script-generator
description: Generates 60-180 second YouTube Shorts scripts for 认知提升 channel. Creates pattern-interrupt hooks, concrete examples, action steps. Outputs structured JSON with metadata. Use when creating shorts content, saying "write a short about [topic]", or in automated pipeline.
---

# Shorts Script Generator

Generates high-quality vertical video scripts (130-260 words) with hooks that stop scrolling.

## Script Structure

1. **Hook** (first 3-5s) — Pattern interrupt, max 12 words
2. **Key insight** — 1-2 core points only
3. **Concrete example** — Micro story or illustration
4. **Action step** — Specific, doable today
5. **CTA** — "Follow for 1 idea/day" (7-10 words)

## Generate Script

Provide book and angle, get structured output:

```json
{
  "title": "Stop Chasing Goals. Fix Your Identity.",
  "hook": "Rich people don't chase goals. They change who they are.",
  "script": "Rich people don't chase goals...\n\nThey change who they are first...",
  "action_step": "Write down: I am a person who [habit]. Read it every morning.",
  "hashtags": ["#认知", "#mindset", "#habits", "#identity"],
  "estimated_duration_sec": 95,
  "word_count": 185
}
```

## Prompt Template

Use this when calling LLM:

```
Write a 60-180 second vertical script (130-260 words) for 认知提升 YouTube channel.

BOOK: {{title}} by {{authors}}
ANGLE: {{angle}}

STRUCTURE:
1. Hook (pattern interrupt, max 12 words)
2. Core insight (1-2 key points)
3. Concrete example or micro story
4. Action step (specific, doable today)
5. Close: "Follow for 1 idea/day"

STYLE:
- Clear, direct, no jargon
- One idea per sentence
- Use "you" not "we"
- Contractions for natural flow

OUTPUT: JSON with title, hook, script, action_step, hashtags, estimated_duration_sec
```

## Hook Patterns

See [references/hook_patterns.md](references/hook_patterns.md) for 10 proven patterns:
- Contrarian: "Rich people don't save first"
- Question: "Ever notice how..."
- Story: "I tried this for 30 days"
- Challenge: "Most people get this wrong"

## Quality Checklist

Before passing to TTS:
- [ ] Word count 130-260
- [ ] Hook ≤12 words
- [ ] Has concrete example
- [ ] Action step is specific
- [ ] No generic phrases ("in today's video")