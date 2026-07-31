"""yt_list — list the channel's videos grouped by status (scheduled / private / unlisted /
public), using the same saved token as upload.py. Needs the youtube.readonly scope
(added to upload.py SCOPES; re-run `python scripts/upload.py --auth` once to grant it).

Usage:  python scripts/yt_list.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload import get_creds  # shared auth (token + client)


def main() -> None:
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", credentials=get_creds())

    # the authenticated user's own videos (includes private + scheduled)
    ids, req = [], yt.search().list(part="id", forMine=True, type="video", maxResults=50, order="date")
    while req is not None:
        r = req.execute()
        ids += [it["id"]["videoId"] for it in r.get("items", []) if it["id"].get("videoId")]
        req = yt.search().list_next(req, r)

    rows = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,status,statistics", id=",".join(ids[i:i + 50])).execute()
        for v in r["items"]:
            st, sn = v["status"], v["snippet"]
            rows.append({
                "id": v["id"], "title": sn["title"],
                "privacy": st.get("privacyStatus"),
                "publishAt": st.get("publishAt"),          # set only on scheduled
                "published": sn.get("publishedAt"),
                "views": v.get("statistics", {}).get("viewCount", "—"),
            })

    def show(label, items, extra=lambda r: ""):
        if not items:
            return
        print(f"\n=== {label} ({len(items)}) ===")
        for r in sorted(items, key=lambda x: x.get("publishAt") or x.get("published") or ""):
            print(f"  {r['title'][:60]:<60} {extra(r)}  https://youtu.be/{r['id']}")

    scheduled = [r for r in rows if r["privacy"] == "private" and r["publishAt"]]
    private = [r for r in rows if r["privacy"] == "private" and not r["publishAt"]]
    unlisted = [r for r in rows if r["privacy"] == "unlisted"]
    public = [r for r in rows if r["privacy"] == "public"]

    print(f"\n{len(rows)} videos on the channel.")
    show("SCHEDULED", scheduled, lambda r: f"→ publishes {r['publishAt']}")
    show("PRIVATE (no schedule)", private)
    show("UNLISTED", unlisted)
    show("PUBLIC", public, lambda r: f"{r['views']} views")


if __name__ == "__main__":
    main()
