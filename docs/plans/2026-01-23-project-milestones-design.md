# Project Milestones: Start to Production

**Project:** 认知提升 / Cognitive Uplift - YouTube Book Summary Automation
**Date:** 2026-01-23
**Approach:** Vertical Slice (build thin working pipeline, then expand)

## Overview

Semi-automated YouTube channel for book summaries. System handles heavy lifting (scripts, TTS, rendering), human reviews and approves before upload. Starts local, scales to cloud if proven.

**Content types:** Shorts (60-180s) + Midform (20-60min) from day one
**Visual style:** AI-generated Da Vinci oil painting art
**Target audience:** 18-35 year olds interested in self-improvement

---

## Milestone 0: Foundation Setup

**Goal:** Everything needed before generating content.

### Deliverables

1. **YouTube channel**
   - Channel name: 认知提升
   - Brand account (not personal) for flexibility
   - YouTube Data API enabled in Google Cloud Console

2. **API keys**
   - OpenAI API key (DALL-E for images)
   - ElevenLabs API key (TTS)
   - YouTube Data API credentials (OAuth for uploads)

3. **Project structure**
   ```
   proj_cogni/
   ├── .claude/skills/     # Agent skills (done)
   ├── data/
   │   ├── books.json      # Book catalog
   │   └── videos/         # Video job tracking
   ├── assets/
   │   ├── images/         # Generated Da Vinci art
   │   └── audio/          # TTS output
   ├── output/             # Rendered videos
   └── scripts/            # Generated scripts
   ```

4. **Initial book list** - 5-10 books to start

5. **Local dependencies** - ffmpeg, Python packages, Whisper

### Exit Criteria
- Can authenticate to all APIs
- Folder structure exists
- Dependencies installed

---

## Milestone 1: MVP Short

**Goal:** One complete short, from book selection to uploaded video.

### Pipeline

| Step | You Do | System Does |
|------|--------|-------------|
| 1. Select | Pick book + angle | Dedup check |
| 2. Script | Review, approve/feedback | Generate + internal quality checks |
| 3. Assets | Review images | Generate Da Vinci art from script |
| 4. Audio | Review | TTS + normalize to -16 LUFS |
| 5. Video | Review final | Render 1080x1920 with captions |
| 6. Upload | Final approve | Upload to YouTube |

### Details

- **Script generation:** Skill handles hook, structure, quality, copyright internally. You review output and give feedback. Iterate until satisfied.
- **Assets:** 3-5 Da Vinci style images extracted from script scenes
- **Video:** Ken Burns effect on images, auto-captions via Whisper

### Exit Criteria
- One short is live on YouTube

---

## Milestone 2: Add Midform

**Goal:** Extend pipeline to 20-60 minute deep dive videos.

### Differences from Shorts

| Aspect | Short | Midform |
|--------|-------|---------|
| Duration | 60-180 sec | 20-60 min |
| Script | Single hook + payoff | Chapters (cold open, 4-5 sections, action steps) |
| Images | 3-5 scenes | 20-40 scenes |
| Orientation | 9:16 vertical | 16:9 landscape |
| Thumbnail | Not critical | Required for CTR |
| Chapters | N/A | YouTube chapters in description |

### New Components

1. **Midform script generator** - Chapter structure with timestamps
2. **Thumbnail generator** - Book cover + bold hook text
3. **Batch image generation** - 20-40 images with pacing logic
4. **Extended render** - Same ffmpeg, more inputs, chapter markers

### Exit Criteria
- One midform video (20+ min) is live on YouTube

---

## Milestone 3: Polish & Automate

**Goal:** Reduce friction based on learnings from first videos.

### Improvements

1. **Single CLI command**
   ```bash
   ./cogni short "Atomic Habits" "the 2-minute rule"
   ./cogni midform "Deep Work"
   ```
   Orchestrates all steps, pauses for review at key points.

2. **Feedback loop**
   - Scripts you edited → update skill prompts
   - Images that missed → refine Da Vinci prompt
   - Save "golden examples" as references

3. **Content calendar integration**
   - Plan week ahead
   - Track in-progress vs published
   - Prevent duplicate topics automatically

### Exit Criteria
- "I want to make a video about X" → "video uploaded" with minimal friction

---

## Milestone 4: Admin Panel

**Goal:** Simple web UI to manage pipeline without CLI.

### Features

| Feature | Purpose |
|---------|---------|
| Content calendar | See planned/in-progress/published videos |
| Review queue | Approve scripts, images, final videos |
| Book catalog | Browse books, see coverage, add new ones |
| Pipeline status | What's generating, what's waiting |
| Quick actions | "New short", "New midform" buttons |

### Tech

- Local web app (Next.js or Flask)
- Reads/writes same `data/` files as CLI
- No auth (local only)

### Exit Criteria
- Can manage full workflow from browser

---

## Milestone 5: Analytics Loop

**Goal:** Let performance data inform content decisions.

### Components

1. **Metrics pulling**
   - Fetch YouTube analytics daily (24h after upload)
   - Track: views, CTR, avg view %, likes, comments, subscribers
   - Store in `data/metrics/`

2. **Success scoring**
   - Calculate score per video
   - Flag underperformers (CTR < 2%, retention < 30%)
   - Identify patterns: which books/angles/hooks work

3. **A/B testing**
   - Test hook styles on every ~10th short
   - Track winning variants
   - Feed learnings back into script generator

4. **Pivot detection**
   - Weekly review: growing or stalling?
   - Surface recommendations if 4-week trend negative
   - "CTR declining → test new thumbnail style"

5. **Book catalog updates**
   - Mark books as "hot" or "cold"
   - Influence future content selection
   - Prevent oversaturation

### Exit Criteria
- Weekly routine where data informs next content decisions

---

## Summary

| Milestone | Goal | Key Outcome |
|-----------|------|-------------|
| M0 | Foundation | APIs ready, structure set |
| M1 | MVP Short | First short live |
| M2 | Add Midform | First midform live |
| M3 | Polish | Streamlined CLI workflow |
| M4 | Admin Panel | Web UI for management |
| M5 | Analytics | Data-driven decisions |

**Principle:** Build the thinnest working slice first (M1), learn from real YouTube feedback, then expand. Avoid over-engineering before validation.