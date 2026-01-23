#!/usr/bin/env python3
"""
Upload video to YouTube via Data API v3.

Usage:
    python upload_to_youtube.py --video video.mp4 --title "Title" --description desc.txt --tags "tag1,tag2"

Requires:
    - credentials.json (OAuth client credentials)
    - google-auth-oauthlib, google-api-python-client packages
"""

import argparse
import json
import os
import time
from pathlib import Path

# Try to import Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"


def get_authenticated_service():
    """Get authenticated YouTube service."""
    if not GOOGLE_API_AVAILABLE:
        raise ImportError("Google API libraries not installed. Run: pip install google-auth-oauthlib google-api-python-client")

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list,
    visibility: str = "private",
    thumbnail_path: Path = None,
    max_retries: int = 3
) -> dict:
    """Upload video to YouTube with retries."""

    if not GOOGLE_API_AVAILABLE:
        # Return mock response for testing without API
        return {
            "mock": True,
            "video_id": "mock_video_id",
            "url": "https://youtube.com/watch?v=mock_video_id",
            "message": "Google API not available - mock response"
        }

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"  # People & Blogs
        },
        "status": {
            "privacyStatus": visibility,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024  # 1MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    # Upload with retries
    response = None
    retry = 0

    while response is None and retry < max_retries:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        except Exception as e:
            retry += 1
            if retry < max_retries:
                sleep_time = 2 ** retry
                print(f"Error uploading, retry {retry}/{max_retries} in {sleep_time}s: {e}")
                time.sleep(sleep_time)
            else:
                raise

    video_id = response["id"]

    # Upload thumbnail if provided
    if thumbnail_path and thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path))
            ).execute()
        except Exception as e:
            print(f"Warning: Failed to upload thumbnail: {e}")

    return {
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "visibility": visibility
    }


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--tags", required=True, help="Comma-separated tags")
    parser.add_argument("--visibility", default="private", choices=["public", "private", "unlisted"])
    parser.add_argument("--thumbnail", type=Path)
    args = parser.parse_args()

    description = args.description.read_text() if args.description.exists() else ""
    tags = [t.strip() for t in args.tags.split(",")]

    result = upload_video(
        video_path=args.video,
        title=args.title,
        description=description,
        tags=tags,
        visibility=args.visibility,
        thumbnail_path=args.thumbnail
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()