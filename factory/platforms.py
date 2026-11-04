"""Upload to YouTube Shorts, Instagram Reels and Facebook Reels, and read back stats.

All keys come from GitHub secrets. Each page has its own prefixed secrets
(CURIOUS_..., DRAMA_...), passed in here as `p`.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from .channels import secret

GRAPH = os.environ.get("META_GRAPH_VERSION", "v24.0")


def _need(p: str, name: str) -> str:
    v = secret(p, name)
    if not v:
        raise RuntimeError(f"Missing secret {name if name in ('YT_CLIENT_ID', 'YT_CLIENT_SECRET') else p + name}")
    return v


# ---------------- YouTube ----------------

def _yt_token(p: str) -> str:
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": _need(p, "YT_CLIENT_ID"),
        "client_secret": _need(p, "YT_CLIENT_SECRET"),
        "refresh_token": _need(p, "YT_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def youtube_upload(p: str, video: Path, meta: dict) -> dict:
    token = _yt_token(p)
    yt = meta["youtube"]
    body = {
        "snippet": {"title": yt["title"][:100], "description": yt["description"],
                    "tags": yt.get("tags", []), "categoryId": yt.get("category", "24")},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True},
    }
    size = video.stat().st_size
    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
        data=json.dumps(body), timeout=60)
    r.raise_for_status()
    with video.open("rb") as f:
        up = requests.put(r.headers["Location"], data=f,
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"},
                          timeout=900)
    up.raise_for_status()
    res = up.json()
    return {"id": res["id"], "url": f"https://youtube.com/shorts/{res['id']}",
            "privacy": res.get("status", {}).get("privacyStatus")}


def youtube_stats(p: str, ids: list[str]) -> dict:
    if not ids:
        return {}
    token = _yt_token(p)
    out = {}
    for i in range(0, len(ids), 50):
        r = requests.get("https://www.googleapis.com/youtube/v3/videos",
                         params={"part": "statistics,status", "id": ",".join(ids[i:i + 50])},
                         headers={"Authorization": f"Bearer {token}"}, timeout=30)
        r.raise_for_status()
        for it in r.json().get("items", []):
            s = it["statistics"]
            out[it["id"]] = {"views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                             "comments": int(s.get("commentCount", 0)),
                             "privacy": it["status"]["privacyStatus"]}
    return out


# ---------------- Meta (Instagram + Facebook) ----------------

def _rupload(p: str, url: str, video: Path) -> dict:
    size = video.stat().st_size
    with video.open("rb") as f:
        r = requests.post(url, data=f, timeout=900, headers={
            "Authorization": f"OAuth {_need(p, 'META_PAGE_TOKEN')}", "offset": "0", "file_size": str(size)})
    r.raise_for_status()
    return r.json()


def instagram_upload(p: str, video: Path, meta: dict) -> dict:
    ig, tok = _need(p, "IG_USER_ID"), _need(p, "META_PAGE_TOKEN")
    base = f"https://graph.facebook.com/{GRAPH}"
    r = requests.post(f"{base}/{ig}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": meta["instagram"]["caption"],
        "share_to_feed": "true", "access_token": tok}, timeout=60)
    r.raise_for_status()
    container = r.json()["id"]
    _rupload(p, f"https://rupload.facebook.com/ig-api-upload/{GRAPH}/{container}", video)

    for _ in range(60):  # Instagram processes the video before it can be published
        s = requests.get(f"{base}/{container}", params={"fields": "status_code,status",
                                                       "access_token": tok}, timeout=30).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram processing failed: {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram processing timed out")

    pub = requests.post(f"{base}/{ig}/media_publish", data={"creation_id": container, "access_token": tok},
                        timeout=60)
    pub.raise_for_status()
    media_id = pub.json()["id"]
    link = requests.get(f"{base}/{media_id}", params={"fields": "permalink", "access_token": tok},
                        timeout=30).json().get("permalink")
    return {"id": media_id, "url": link}


def facebook_upload(p: str, video: Path, meta: dict) -> dict:
    page, tok = _need(p, "FB_PAGE_ID"), _need(p, "META_PAGE_TOKEN")
    base = f"https://graph.facebook.com/{GRAPH}/{page}/video_reels"
    r = requests.post(base, data={"upload_phase": "start", "access_token": tok}, timeout=60)
    r.raise_for_status()
    vid = r.json()["video_id"]
    _rupload(p, f"https://rupload.facebook.com/video-upload/{GRAPH}/{vid}", video)
    f = requests.post(base, data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                  "description": meta["facebook"]["description"], "access_token": tok},
                      timeout=60)
    f.raise_for_status()
    return {"id": vid, "url": f"https://www.facebook.com/reel/{vid}"}


def instagram_stats(p: str, media_id: str) -> dict:
    base, tok = f"https://graph.facebook.com/{GRAPH}", _need(p, "META_PAGE_TOKEN")
    out = {}
    basic = requests.get(f"{base}/{media_id}", params={"fields": "like_count,comments_count",
                                                       "access_token": tok}, timeout=30).json()
    out["likes"] = basic.get("like_count", 0)
    out["comments"] = basic.get("comments_count", 0)
    # Metric names change between API versions, so ask one at a time and skip what fails.
    for m in ["views", "reach", "shares", "saved", "ig_reels_avg_watch_time"]:
        r = requests.get(f"{base}/{media_id}/insights", params={"metric": m, "access_token": tok},
                         timeout=30).json()
        try:
            out[m] = r["data"][0]["values"][0]["value"]
        except (KeyError, IndexError):
            pass
    return out


def facebook_stats(p: str, video_id: str) -> dict:
    base, tok = f"https://graph.facebook.com/{GRAPH}", _need(p, "META_PAGE_TOKEN")
    out = {}
    r = requests.get(f"{base}/{video_id}/video_insights", params={"access_token": tok}, timeout=30).json()
    for item in r.get("data", []):
        if item.get("name") in ("blue_reels_play_count", "post_impressions_unique",
                                "post_video_avg_time_watched", "post_video_social_actions"):
            try:
                out[item["name"]] = item["values"][0]["value"]
            except (KeyError, IndexError):
                pass
    return out


UPLOADERS = {"youtube": youtube_upload, "instagram": instagram_upload, "facebook": facebook_upload}


def enabled_platforms(p: str) -> list[str]:
    """A platform runs only once that page's secrets are added, so setup can go one at a time."""
    ok = []
    if secret(p, "YT_REFRESH_TOKEN"):
        ok.append("youtube")
    if secret(p, "META_PAGE_TOKEN") and secret(p, "IG_USER_ID"):
        ok.append("instagram")
    if secret(p, "META_PAGE_TOKEN") and secret(p, "FB_PAGE_ID"):
        ok.append("facebook")
    return ok
