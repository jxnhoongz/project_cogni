#!/usr/bin/env python3
"""
Verify project setup is complete.

Usage: python verify_setup.py
"""

import json
import shutil
from pathlib import Path


def check_directories():
    """Check required directories exist."""
    required = [
        "cogni",
        "cogni/scripts",
        "cogni/generators",
        "cogni/renderers",
        "cogni/uploaders",
        "data",
        "data/videos",
        "assets",
        "assets/images",
        "assets/audio",
        "output",
        "credentials",
        "tests",
    ]
    missing = [d for d in required if not Path(d).is_dir()]
    return missing


def check_files():
    """Check required files exist."""
    required = [
        "data/books.json",
        "requirements.txt",
        ".gitignore",
        ".env.example",
        "cogni/__init__.py",
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
    missing = [
        k for k in required_keys if k not in content or f"{k}=sk-your" in content
    ]
    return missing


def check_ffmpeg():
    """Check ffmpeg is installed."""
    return shutil.which("ffmpeg") is not None


def check_python_deps():
    """Check if key Python packages are importable."""
    missing = []
    packages = [("dotenv", "python-dotenv"), ("openai", "openai"), ("requests", "requests")]
    for pkg, pip_name in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pip_name)
    return missing


def main():
    print("=" * 50)
    print("Project Setup Verification")
    print("=" * 50)

    all_good = True

    # Directories
    missing_dirs = check_directories()
    if missing_dirs:
        print(f"\n[X] Missing directories: {missing_dirs}")
        all_good = False
    else:
        print("\n[OK] All directories present")

    # Files
    missing_files = check_files()
    if missing_files:
        print(f"[X] Missing files: {missing_files}")
        all_good = False
    else:
        print("[OK] All required files present")

    # books.json
    books_error = check_books_json()
    if books_error:
        print(f"[X] books.json error: {books_error}")
        all_good = False
    else:
        with open("data/books.json") as f:
            count = len(json.load(f)["books"])
        print(f"[OK] books.json valid ({count} books)")

    # Environment
    env_missing = check_env()
    if env_missing:
        print(f"[!] Environment: {env_missing}")
    else:
        print("[OK] .env configured")

    # ffmpeg
    if check_ffmpeg():
        print("[OK] ffmpeg installed")
    else:
        print("[X] ffmpeg not found (install via: brew install ffmpeg)")
        all_good = False

    # Python deps
    missing_deps = check_python_deps()
    if missing_deps:
        print(f"[!] Missing Python packages: {missing_deps}")
        print("    Run: pip install -r requirements.txt")
    else:
        print("[OK] Python dependencies installed")

    print("\n" + "=" * 50)
    if all_good:
        print("[OK] Setup complete! Ready for Milestone 1.")
    else:
        print("[X] Setup incomplete. Fix issues above.")
    print("=" * 50)


if __name__ == "__main__":
    main()
