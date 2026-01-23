---
name: midform-script-generator
description: Generates 20-60 minute deep dive scripts for 认知提升 channel. Creates chapter-based structure with cold open, 4-5 chapters, 7-day experiment. Outputs 8000-10000 words with timestamps. Use when creating midform content, saying "create deep dive on [book]", or in automated pipeline.
---

# Midform Script Generator

Generates comprehensive book analysis videos (8000-10000 words) with chapter structure.

## Script Structure

1. **Cold open** (20-30s) — Problem + promise
2. **Book context** — Why this matters now
3. **4-5 chapters** — Each: idea → story → application
4. **7-day experiment** — Specific challenge
5. **Recap** — Key takeaways

## Generate Script

### Step 1: Generate Outline

```
Create outline for 30-45 minute video about {{book}} by {{author}}.

Include:
- Cold open hook
- 4-5 chapter titles (action-oriented)
- Key idea per chapter
- 7-day experiment idea
```

### Step 2: Generate Each Chapter

```
Write chapter {{N}} for {{book}} video.

CHAPTER TITLE: {{title}}
KEY IDEA: {{idea}}

Include:
- Core concept (1 paragraph)
- Story/example (2-3 paragraphs)
- Application (what to try this week)

STYLE: Calm mentor voice, zero fluff, high signal
Keep quotes brief (<50 words) and attributed.
```

### Step 3: Polish and Timestamps

Generate final output:

```json
{
  "title": "Atomic Habits: The Science of Tiny Changes",
  "chapters": [
    {
      "title": "Why 1% Improvements Beat Big Goals",
      "timestamp": "0:00",
      "word_count": 1800,
      "script": "..."
    }
  ],
  "seven_day_experiment": "Track one keystone habit daily...",
  "description": "...",
  "hashtags": ["#认知", "#atomichabits", "#habits"],
  "total_word_count": 9200,
  "estimated_duration_min": 38
}
```

## Chapter Frameworks

See [references/chapter_structures.md](references/chapter_structures.md):
- Problem → Solution → Evidence → Application
- Story → Principle → Counter-example → Action
- Myth → Reality → Why it matters → How to apply

## Quality Standards

- 8000-10000 total words
- 150 words/minute for duration estimate
- Each chapter 1500-2500 words
- Quotes <50 words with attribution
- Max 1 rhetorical question per chapter
