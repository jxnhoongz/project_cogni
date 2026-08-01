"""upload — push a finished video (long-form or short) to YouTube via the Data API v3.

Kills the grunt work (dragging the file, pasting title/description/tags, setting the
thumbnail) WITHOUT taking away the review step: it uploads **private by default**, so the
video lands on the channel unlisted-to-the-world and Jin eyeballs it in Studio and hits
Publish (or schedules a publish time here and reviews before it fires). Automation of the
tedium, not the judgment.

One-time setup (already done if credentials/youtube_client.json exists):
  Google Cloud → enable YouTube Data API v3 → OAuth Desktop client → download JSON →
  save as credentials/youtube_client.json (gitignored). No billing needed.

First run does a browser consent once and saves credentials/youtube.token.json:
  python scripts/upload.py --auth

Then upload from a spec JSON:
  python scripts/upload.py uploads/<name>.json
  # spec: { "video": "<path>", "title": "...", "description": "...", "tags": ["..."],
  #         "categoryId": "27", "privacy": "private"|"unlisted"|"public",
  #         "publishAt": "2026-08-01T14:00:00Z"   (optional; forces private, auto-publishes),
  #         "thumbnail": "<path>"  (optional), "playlistId": "..."  (optional) }
  python scripts/upload.py uploads/<name>.json --dry-run   # validate everything, upload nothing

Quota: an upload costs ~1600 of the 10,000/day free units (~6 uploads/day). Plenty.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CRED = REPO / "credentials"
CLIENT = CRED / "youtube_client.json"
TOKEN = CRED / "youtube.token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]   # readonly = list/inspect own videos


def get_creds(force_consent: bool = False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CLIENT.exists():
        raise SystemExit(f"missing {CLIENT} — download the OAuth Desktop client JSON there first.")
    creds = None
    if TOKEN.exists() and not force_consent:
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("[upload] opening a browser for one-time consent — sign in, then "
                  "Advanced → Continue past the 'unverified app' warning → Allow ...")
            creds = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES).run_local_server(port=0)
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
        print(f"[upload] token saved -> {TOKEN.relative_to(REPO)}")
    return creds


def upload(spec_path: Path, dry_run: bool) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    video = Path(spec["video"])
    if not video.is_absolute():
        video = REPO / video
    if not video.exists():
        raise SystemExit(f"video not found: {video}")
    thumb = spec.get("thumbnail")
    if thumb:
        thumb = Path(thumb) if Path(thumb).is_absolute() else REPO / thumb
        if not thumb.exists():
            raise SystemExit(f"thumbnail not found: {thumb}")

    privacy = spec.get("privacy", "private")
    publish_at = spec.get("publishAt")
    if publish_at:
        privacy = "private"        # YouTube: scheduled videos must be private until publishAt
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": bool(spec.get("madeForKids", False))}
    if publish_at:
        status["publishAt"] = publish_at
    body = {
        "snippet": {
            "title": spec["title"],
            "description": spec.get("description", ""),
            "tags": spec.get("tags", []),
            "categoryId": str(spec.get("categoryId", "27")),   # 27 = Education
        },
        "status": status,
    }
    size_mb = video.stat().st_size / 1e6
    print(f"[upload] {video.name}  ({size_mb:.0f} MB)")
    print(f"         title: {spec['title']}")
    print(f"         privacy: {privacy}" + (f"  publishAt: {publish_at}" if publish_at else "")
          + (f"  thumbnail: {thumb.name}" if thumb else ""))
    if dry_run:
        get_creds()                # refresh/validate auth, but insert nothing
        print("[upload] --dry-run: spec + files + auth OK, nothing uploaded.")
        return

    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    yt = build("youtube", "v3", credentials=get_creds())
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        prog, resp = req.next_chunk()
        if prog:
            print(f"\r         uploading… {int(prog.progress() * 100)}%", end="", flush=True)
    vid = resp["id"]
    print(f"\r         uploaded: https://youtu.be/{vid}            ")

    if thumb:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        print("         thumbnail set.")
    if spec.get("playlistId"):
        yt.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": spec["playlistId"], "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        print("         added to playlist.")
    print(f"[upload] done — review it in YouTube Studio, then Publish (or it auto-publishes at publishAt).")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?", help="upload spec JSON")
    ap.add_argument("--auth", action="store_true", help="do the one-time browser consent and exit")
    ap.add_argument("--dry-run", action="store_true", help="validate spec + files + auth, upload nothing")
    a = ap.parse_args()
    if a.auth:
        get_creds(force_consent=not TOKEN.exists())
        print("[upload] auth OK.")
        return
    if not a.spec:
        ap.error("give a spec JSON, or --auth for the one-time consent")
    upload(Path(a.spec), a.dry_run)


if __name__ == "__main__":
    main()
