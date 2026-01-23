# Milestone 0: Foundation Setup - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up project structure, dependencies, and initial data files so we can start generating content.

**Architecture:** Local-first setup with Python scripts, ffmpeg for video, and JSON files for data storage. API keys stored in `.env` file.

**Tech Stack:** Python 3.11+, ffmpeg, openai, elevenlabs, google-api-python-client

---

## Task 1: Create Project Directory Structure

**Files:**
- Create: `data/books.json`
- Create: `data/videos/.gitkeep`
- Create: `assets/images/.gitkeep`
- Create: `assets/audio/.gitkeep`
- Create: `output/.gitkeep`
- Create: `scripts/.gitkeep`

**Step 1: Create directories**

```bash
mkdir -p data/videos assets/images assets/audio output scripts
```

**Step 2: Create .gitkeep files to preserve empty directories**

```bash
touch data/videos/.gitkeep assets/images/.gitkeep assets/audio/.gitkeep output/.gitkeep scripts/.gitkeep
```

**Step 3: Verify structure**

Run: `find . -type d -not -path './.claude*' -not -path './.git*' | sort`

Expected:
```
.
./assets
./assets/audio
./assets/images
./data
./data/videos
./docs
./docs/plans
./output
./scripts
```

---

## Task 2: Create Initial Books Catalog

**Files:**
- Create: `data/books.json`

**Step 1: Create books.json with starter books**

```json
{
  "books": [
    {
      "id": "atomic-habits",
      "title": "Atomic Habits",
      "author": "James Clear",
      "category": "habits",
      "angles": [
        "the-2-minute-rule",
        "habit-stacking",
        "1-percent-better",
        "environment-design",
        "identity-based-habits"
      ],
      "coverage": []
    },
    {
      "id": "deep-work",
      "title": "Deep Work",
      "author": "Cal Newport",
      "category": "productivity",
      "angles": [
        "shallow-vs-deep",
        "attention-residue",
        "rhythmic-philosophy",
        "grand-gestures",
        "embrace-boredom"
      ],
      "coverage": []
    },
    {
      "id": "thinking-fast-and-slow",
      "title": "Thinking, Fast and Slow",
      "author": "Daniel Kahneman",
      "category": "psychology",
      "angles": [
        "system-1-vs-system-2",
        "cognitive-biases",
        "anchoring-effect",
        "loss-aversion",
        "peak-end-rule"
      ],
      "coverage": []
    },
    {
      "id": "the-psychology-of-money",
      "title": "The Psychology of Money",
      "author": "Morgan Housel",
      "category": "finance",
      "angles": [
        "wealth-vs-rich",
        "compounding",
        "room-for-error",
        "man-in-the-car-paradox",
        "saving-without-reason"
      ],
      "coverage": []
    },
    {
      "id": "cant-hurt-me",
      "title": "Can't Hurt Me",
      "author": "David Goggins",
      "category": "mindset",
      "angles": [
        "40-percent-rule",
        "accountability-mirror",
        "callousing-your-mind",
        "taking-souls",
        "cookie-jar-method"
      ],
      "coverage": []
    }
  ],
  "categories": ["habits", "productivity", "psychology", "finance", "mindset"],
  "last_updated": "2026-01-23"
}
```

**Step 2: Verify JSON is valid**

Run: `python -m json.tool data/books.json > /dev/null && echo "Valid JSON"`

Expected: `Valid JSON`

---

## Task 3: Create Environment Configuration

**Files:**
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Create .env.example template**

```bash
# OpenAI API (for DALL-E image generation)
OPENAI_API_KEY=sk-your-key-here

# ElevenLabs API (for TTS)
ELEVENLABS_API_KEY=your-key-here

# YouTube API (OAuth credentials path)
YOUTUBE_CLIENT_SECRETS=credentials/client_secrets.json

# Optional: anthropic for script generation
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Step 2: Create .gitignore**

```gitignore
# Environment
.env
.env.local

# Credentials
credentials/
*.json
!data/books.json
!package.json

# Generated content
assets/images/*
!assets/images/.gitkeep
assets/audio/*
!assets/audio/.gitkeep
output/*
!output/.gitkeep
scripts/*
!scripts/.gitkeep

# Python
__pycache__/
*.pyc
.venv/
venv/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

**Step 3: Create credentials directory**

```bash
mkdir -p credentials
echo "Place YouTube OAuth client_secrets.json here" > credentials/README.md
```

---

## Task 4: Create Python Dependencies File

**Files:**
- Create: `requirements.txt`

**Step 1: Create requirements.txt**

```txt
# Core
python-dotenv>=1.0.0

# OpenAI (DALL-E)
openai>=1.0.0

# ElevenLabs (TTS)
elevenlabs>=1.0.0

# YouTube API
google-api-python-client>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0

# Audio processing
pydub>=0.25.0

# Whisper for captions
openai-whisper>=20231117

# Utilities
requests>=2.31.0
```

**Step 2: Verify file exists**

Run: `cat requirements.txt | head -5`

Expected: Shows first 5 lines of requirements

---

## Task 5: Create Setup Verification Script

**Files:**
- Create: `verify_setup.py`

**Step 1: Create verification script**

```python
#!/usr/bin/env python3
"""
Verify project setup is complete.

Usage: python verify_setup.py
"""

import os
import json
import shutil
from pathlib import Path

def check_directories():
    """Check required directories exist."""
    required = [
        "data", "data/videos",
        "assets", "assets/images", "assets/audio",
        "output", "scripts", "credentials"
    ]
    missing = [d for d in required if not Path(d).is_dir()]
    return missing

def check_files():
    """Check required files exist."""
    required = [
        "data/books.json",
        "requirements.txt",
        ".gitignore",
        ".env.example"
    ]
    missing = [f for f in required if not Path(f).is_file()]
    return missing

def check_books_json():
    """Validate books.json structure."""
    try:
        with open("data/books.json") as f:
            data = json.load(f)
        if "books" not in data:
            return "Missing 'books' key"
        if len(data["books"]) == 0:
            return "No books in catalog"
        return None
    except Exception as e:
        return str(e)

def check_env():
    """Check if .env exists with required keys."""
    if not Path(".env").is_file():
        return ["No .env file (copy from .env.example)"]

    with open(".env") as f:
        content = f.read()

    required_keys = ["OPENAI_API_KEY"]
    missing = [k for k in required_keys if k not in content or f"{k}=sk-your" in content]
    return missing

def check_ffmpeg():
    """Check ffmpeg is installed."""
    return shutil.which("ffmpeg") is not None

def check_python_deps():
    """Check if key Python packages are importable."""
    missing = []
    packages = ["dotenv", "openai", "requests"]
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing

def main():
    print("=" * 50)
    print("Project Setup Verification")
    print("=" * 50)

    all_good = True

    # Directories
    missing_dirs = check_directories()
    if missing_dirs:
        print(f"\n❌ Missing directories: {missing_dirs}")
        all_good = False
    else:
        print("\n✅ All directories present")

    # Files
    missing_files = check_files()
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        all_good = False
    else:
        print("✅ All required files present")

    # books.json
    books_error = check_books_json()
    if books_error:
        print(f"❌ books.json error: {books_error}")
        all_good = False
    else:
        with open("data/books.json") as f:
            count = len(json.load(f)["books"])
        print(f"✅ books.json valid ({count} books)")

    # Environment
    env_missing = check_env()
    if env_missing:
        print(f"⚠️  Environment: {env_missing}")
    else:
        print("✅ .env configured")

    # ffmpeg
    if check_ffmpeg():
        print("✅ ffmpeg installed")
    else:
        print("❌ ffmpeg not found (install via: brew install ffmpeg)")
        all_good = False

    # Python deps
    missing_deps = check_python_deps()
    if missing_deps:
        print(f"⚠️  Missing Python packages: {missing_deps}")
        print("   Run: pip install -r requirements.txt")
    else:
        print("✅ Python dependencies installed")

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Setup complete! Ready for Milestone 1.")
    else:
        print("❌ Setup incomplete. Fix issues above.")
    print("=" * 50)

if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

```bash
chmod +x verify_setup.py
```

---

## Task 6: Install Dependencies and Verify

**Step 1: Create virtual environment (if not exists)**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Step 2: Install Python dependencies**

```bash
pip install -r requirements.txt
```

**Step 3: Verify ffmpeg is installed**

```bash
ffmpeg -version | head -1
```

Expected: `ffmpeg version X.X.X ...`

If missing on macOS:
```bash
brew install ffmpeg
```

**Step 4: Copy .env.example to .env**

```bash
cp .env.example .env
```

Then manually edit `.env` to add your actual API keys.

**Step 5: Run verification**

```bash
python verify_setup.py
```

Expected: All green checkmarks (except API keys if not yet added)

---

## Manual Steps (Outside Code)

These require human action:

1. **Create YouTube channel** at youtube.com
   - Use brand account, not personal
   - Name: 认知提升

2. **Enable YouTube Data API**
   - Go to console.cloud.google.com
   - Create project
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download client_secrets.json to `credentials/`

3. **Get API keys**
   - OpenAI: platform.openai.com/api-keys
   - ElevenLabs: elevenlabs.io (account settings)
   - Add to `.env` file

---

## Exit Criteria Checklist

- [ ] Directory structure exists
- [ ] `data/books.json` has 5 starter books
- [ ] `.env` file with API keys
- [ ] `requirements.txt` with all dependencies
- [ ] Python virtual environment created
- [ ] ffmpeg installed
- [ ] `python verify_setup.py` shows all green
- [ ] YouTube channel created (manual)
- [ ] YouTube API credentials in `credentials/` (manual)