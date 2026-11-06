#!/usr/bin/env python3
"""video-factory: complete YouTube upload script (videos.insert, resumable upload).

This is the exact upload flow our daily GitHub Actions job runs for our own two channels.
Usage:
    YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... \
    python youtube_upload.py final.mp4 "Title #shorts" "Description"

The refresh token comes from a one-time OAuth 2.0 sign-in by the channel owner
(scopes: youtube.upload, youtube.readonly, youtube.force-ssl) and is stored as an encrypted secret.
"""
import json
import os
import sys
from pathlib import Path

import requests


def access_token() -> str:
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def upload(video: Path, title: str, description: str, tags: list[str] | None = None) -> dict:
    token = access_token()
    body = {
        "snippet": {"title": title[:100], "description": description, "tags": tags or [], "categoryId": "27"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True},  # our visuals are AI-made, always labelled
    }
    size = video.stat().st_size
    start = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
        data=json.dumps(body), timeout=60)
    start.raise_for_status()
    with video.open("rb") as f:
        up = requests.put(start.headers["Location"], data=f, timeout=900,
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"})
    up.raise_for_status()
    res = up.json()
    return {"id": res["id"], "url": f"https://youtube.com/shorts/{res['id']}",
            "privacy": res.get("status", {}).get("privacyStatus")}


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("usage: youtube_upload.py VIDEO TITLE DESCRIPTION")
    print(json.dumps(upload(Path(sys.argv[1]), sys.argv[2], sys.argv[3]), indent=2))
