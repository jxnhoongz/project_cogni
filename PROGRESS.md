# Project Progress

## Current State: Milestone 0 Complete

**Last Updated:** 2026-01-23

## What's Done

### Milestone 0: Foundation Setup ✅
- Project structure created (`cogni/`, `data/`, `assets/`, `output/`, `tests/`)
- `data/books.json` with 5 starter books (Atomic Habits, Deep Work, Thinking Fast and Slow, Psychology of Money, Can't Hurt Me)
- Environment config (`.env.example`, `.gitignore`)
- Python dependencies (`requirements.txt`)
- Setup verification script (`verify_setup.py`)
- 18 agent skills in `.claude/skills/`

## What's Next

### Milestone 1: MVP Short
Build first end-to-end short video pipeline:
1. Select book + angle → dedup check
2. Generate script → review/approve
3. Generate Da Vinci style images from script
4. Generate TTS audio
5. Render 1080x1920 vertical video with captions
6. Review and upload to YouTube

## Setup Instructions (New Machine)

```bash
cd "/path/to/proj_cogni"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY (required for DALL-E images)
# - ELEVENLABS_API_KEY (required for TTS)
# - ANTHROPIC_API_KEY (optional, for script generation)

# Verify setup
python verify_setup.py
```

## Key Design Decisions

| Decision | Choice |
|----------|--------|
| Automation | Python scripts |
| Video rendering | ffmpeg |
| Data storage | JSON files (local-first) |
| Image style | AI-generated Da Vinci oil paintings |
| Admin panel (M4) | Direct file access, no separate API |
| Architecture | Semi-automated with human review before upload |

## Milestones Overview

| # | Milestone | Status |
|---|-----------|--------|
| M0 | Foundation Setup | ✅ Complete |
| M1 | MVP Short | 🔜 Next |
| M2 | Add Midform | Pending |
| M3 | Polish & Automate | Pending |
| M4 | Admin Panel | Pending |
| M5 | Analytics Loop | Pending |

## Reference Docs

- [Project Milestones Design](docs/plans/2026-01-23-project-milestones-design.md)
- [Milestone 0 Implementation Plan](docs/plans/2026-01-23-milestone-0-foundation.md)
