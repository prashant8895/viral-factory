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
    if r.status_code >= 400:  # keep Meta's own reason in the error, it says what to fix
        raise RuntimeError(f"Instagram upload refused ({r.status_code}): {r.text[:500]}")
    return r.json()


def _ig_try(p: str, video: Path, media_type: str, caption: str | None, video_url: str | None) -> dict:
    """One attempt: new container, send the video (file upload, or Meta fetches video_url), publish."""
    ig, tok = _need(p, "IG_USER_ID"), _need(p, "META_PAGE_TOKEN")
    base = f"https://graph.facebook.com/{GRAPH}"
    data = {"media_type": media_type, "access_token": tok}
    if video_url:
        data["video_url"] = video_url
    else:
        data["upload_type"] = "resumable"
    if media_type == "REELS":
        data.update(caption=caption or "", share_to_feed="true")
    r = requests.post(f"{base}/{ig}/media", data=data, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram container refused ({r.status_code}): {r.text[:500]}")
    container = r.json()["id"]
    if not video_url:
        _rupload(p, f"https://rupload.facebook.com/ig-api-upload/{GRAPH}/{container}", video)

    for _ in range(60):  # Instagram processes the video before it can be published
        st = requests.get(f"{base}/{container}", params={"fields": "status_code,status",
                                                        "access_token": tok}, timeout=30).json()
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram processing failed: {st}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram processing timed out")

    pub = requests.post(f"{base}/{ig}/media_publish", data={"creation_id": container, "access_token": tok},
                        timeout=60)
    if pub.status_code >= 400:
        raise RuntimeError(f"Instagram publish refused ({pub.status_code}): {pub.text[:500]}")
    media_id = pub.json()["id"]
    link = requests.get(f"{base}/{media_id}", params={"fields": "permalink", "access_token": tok},
                        timeout=30).json().get("permalink")
    return {"id": media_id, "url": link}


def _ig_publish(p: str, video: Path, media_type: str, caption: str | None, video_url: str | None = None) -> dict:
    """Meta's upload endpoint sometimes answers 'ProcessingFailedError' for a file it accepted the day
    before. So: two file uploads (each on a fresh container), then let Meta fetch the public release
    URL itself. Nothing is published until a container is FINISHED, so retries never double-post."""
    if video_url:  # hand Meta the final signed file link, not GitHub's redirect (fresh for 30 min)
        try:
            loc = requests.head(video_url, allow_redirects=False, timeout=30).headers.get("Location")
            video_url = loc or video_url
        except requests.RequestException:
            pass
    tries = [None, None] + ([video_url] if video_url else [])
    err = None
    for i, url in enumerate(tries):
        try:
            return _ig_try(p, video, media_type, caption, url)
        except Exception as e:  # noqa: BLE001 - keep Meta's message, try the next way
            err = e
            print(f"  instagram try {i + 1}/{len(tries)} ({'video_url' if url else 'upload'}) failed: {e}", flush=True)
            if i + 1 < len(tries):
                time.sleep(20)
    raise err


def instagram_upload(p: str, video: Path, meta: dict) -> dict:
    return _ig_publish(p, video, "REELS", meta["instagram"]["caption"], meta.get("video_url"))


def instagram_story_upload(p: str, video: Path, meta: dict) -> dict:
    """The same video as a Story, right after the Reel: gives each post a second way in."""
    return _ig_publish(p, video, "STORIES", None, meta.get("video_url"))


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
    """Reel numbers. Needs the page token to carry read_insights; if Meta refuses, the
    reason is kept in "error" so the numbers review can say exactly what to fix."""
    base, tok = f"https://graph.facebook.com/{GRAPH}", _need(p, "META_PAGE_TOKEN")
    out = {}
    r = requests.get(f"{base}/{video_id}/video_insights", timeout=30, params={
        "metric": "blue_reels_play_count,post_impressions_unique,post_video_avg_time_watched,"
                  "post_video_social_actions,post_video_likes_by_reaction_type",
        "access_token": tok}).json()
    if r.get("error"):
        out["error"] = f"facebook insights: {r['error'].get('message', '')}"[:200]
    for item in r.get("data", []):
        try:
            val = item["values"][0]["value"]
        except (KeyError, IndexError):
            continue
        name = item.get("name")
        if name == "post_video_likes_by_reaction_type" and isinstance(val, dict):
            out["likes"] = sum(val.values())
        elif name == "post_video_social_actions" and isinstance(val, dict):
            out["shares"] = val.get("share", 0)
        elif name == "post_impressions_unique":
            out["reach"] = val
        else:
            out[name] = val
    if "blue_reels_play_count" in out:
        out["views"] = out["blue_reels_play_count"]
    if not out.get("views"):  # fall back to the public counters on the video itself
        b = requests.get(f"{base}/{video_id}", timeout=30, params={
            "fields": "views,likes.summary(true),comments.summary(true)", "access_token": tok}).json()
        if b.get("error"):
            out.setdefault("error", f"facebook video: {b['error'].get('message', '')}"[:200])
        else:
            if b.get("views") is not None:
                out["views"] = b["views"]
            out.setdefault("likes", ((b.get("likes") or {}).get("summary") or {}).get("total_count"))
            out["comments"] = ((b.get("comments") or {}).get("summary") or {}).get("total_count")
    return out


def youtube_retention(p: str, ids: list[str], start: str) -> dict:
    """Average view % and seconds per video (YouTube Analytics). Needs the
    yt-analytics.readonly scope on the refresh token; raises if it's missing."""
    if not ids:
        return {}
    import datetime as _dt
    token = _yt_token(p)
    r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", timeout=30,
                     headers={"Authorization": f"Bearer {token}"},
                     params={"ids": "channel==MINE", "startDate": start,
                             "endDate": _dt.date.today().isoformat(), "dimensions": "video",
                             "metrics": "averageViewPercentage,averageViewDuration,shares,subscribersGained",
                             "filters": "video==" + ",".join(ids[:200])})
    if r.status_code >= 400:
        raise RuntimeError(f"YouTube Analytics HTTP {r.status_code}: {r.text[:200]}")
    out = {}
    for vid, pct, sec, shares, subs in r.json().get("rows", []):
        out[vid] = {"yt_avg_view_pct": round(pct, 1), "yt_avg_view_sec": sec, "shares": shares, "subs_gained": subs}
    return out


UPLOADERS = {"youtube": youtube_upload, "instagram": instagram_upload, "instagram_story": instagram_story_upload,
             "facebook": facebook_upload}


def enabled_platforms(p: str) -> list[str]:
    """A platform runs only once that page's secrets are added, so setup can go one at a time."""
    ok = []
    if secret(p, "YT_REFRESH_TOKEN"):
        ok.append("youtube")
    if secret(p, "META_PAGE_TOKEN") and secret(p, "IG_USER_ID"):
        ok.append("instagram")
        if os.environ.get("IG_STORIES", "on") != "off":
            ok.append("instagram_story")
    if secret(p, "META_PAGE_TOKEN") and secret(p, "FB_PAGE_ID"):
        ok.append("facebook")
    return ok
