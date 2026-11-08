"""Comments in, replies out.

    python -m factory.comments collect   # every comment on our last 14 days of posts -> data/comments.json
    python -m factory.comments reply     # post Claude's replies from data/replies.json, record in data/replied.json

Claude reads data/comments.json to (1) write short, genuine replies (never one generic line for
everyone) into data/replies.json and (2) turn "do one on X" asks into Morning Slate ideas.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

from . import platforms
from .channels import secret
from .publish import IST, load_states, prefix

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MAX_REPLIES_PER_RUN = 40
G = lambda: f"https://graph.facebook.com/{platforms.GRAPH}"  # noqa: E731


def _load(name: str, default):
    f = DATA / name
    return json.loads(f.read_text()) if f.exists() else default


def _yt_comments(p: str, video_id: str) -> list[dict]:
    tok = platforms._yt_token(p)
    r = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", timeout=30,
                     headers={"Authorization": f"Bearer {tok}"},
                     params={"part": "snippet,replies", "videoId": video_id, "maxResults": 100, "order": "time"})
    if r.status_code == 403 and "disabled" in r.text:
        return []
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    out = []
    for it in r.json().get("items", []):
        top = it["snippet"]["topLevelComment"]
        sn = top["snippet"]
        ours = any(c["snippet"].get("authorChannelId", {}).get("value") == sn.get("channelId")
                   for c in it.get("replies", {}).get("comments", []))
        out.append({"comment_id": top["id"], "author": sn.get("authorDisplayName"),
                    "text": sn.get("textOriginal", ""), "time": sn.get("publishedAt"),
                    "likes": sn.get("likeCount", 0), "has_our_reply": ours})
    return out


def _ig_comments(p: str, media_id: str) -> list[dict]:
    tok = secret(p, "META_PAGE_TOKEN")
    me = (secret(p, "IG_USER_ID") or "")
    r = requests.get(f"{G()}/{media_id}/comments", timeout=30, params={
        "fields": "id,text,username,timestamp,like_count,replies{username,from}", "access_token": tok})
    r.raise_for_status()
    out = []
    for c in r.json().get("data", []):
        reps = c.get("replies", {}).get("data", [])
        ours = any((x.get("from") or {}).get("id") == me for x in reps)
        out.append({"comment_id": c["id"], "author": c.get("username"), "text": c.get("text", ""),
                    "time": c.get("timestamp"), "likes": c.get("like_count", 0), "has_our_reply": ours})
    return out


def _fb_comments(p: str, video_id: str) -> list[dict]:
    tok, page = secret(p, "META_PAGE_TOKEN"), secret(p, "FB_PAGE_ID")
    r = requests.get(f"{G()}/{video_id}/comments", timeout=30, params={
        "fields": "id,message,from,created_time,like_count,comments{from}", "access_token": tok})
    r.raise_for_status()
    out = []
    for c in r.json().get("data", []):
        if (c.get("from") or {}).get("id") == page:
            continue
        ours = any((x.get("from") or {}).get("id") == page for x in c.get("comments", {}).get("data", []))
        out.append({"comment_id": c["id"], "author": (c.get("from") or {}).get("name"),
                    "text": c.get("message", ""), "time": c.get("created_time"),
                    "likes": c.get("like_count", 0), "has_our_reply": ours})
    return out


READERS = {"youtube": _yt_comments, "instagram": _ig_comments, "facebook": _fb_comments}


def collect() -> None:
    now = datetime.now(IST)
    replied = set(_load("replied.json", {}).keys())
    rows, errors = [], {}
    for s in load_states():
        for name, post in (s.get("platforms") or {}).items():
            if name not in READERS:
                continue
            if now - datetime.fromisoformat(post["posted_at"]) > timedelta(days=14):
                continue
            try:
                for c in READERS[name](prefix(s), post["id"]):
                    c.update(platform=name, channel=s["channel"], video=s["id"], hook=s.get("hook_text"),
                             post_id=post["id"], replied=c["has_our_reply"] or c["comment_id"] in replied)
                    rows.append(c)
            except Exception as e:
                errors[f"{s['channel']}/{name}"] = re.sub(r"(access_token|key)=[^&\s\"']+", r"\1=REDACTED", str(e))[:300]
    rows.sort(key=lambda c: c.get("time") or "", reverse=True)
    DATA.mkdir(exist_ok=True)
    (DATA / "comments.json").write_text(json.dumps(
        {"updated": now.isoformat(timespec="minutes"), "errors": errors, "comments": rows}, indent=2,
        ensure_ascii=False))
    print(f"{len(rows)} comments, {sum(not c['replied'] for c in rows)} waiting for a reply; errors: {errors}")


def _post_reply(r: dict) -> str:
    p = json.loads((ROOT / "channels" / r["channel"] / "channel.json").read_text())["secret_prefix"]
    if r["platform"] == "youtube":
        tok = platforms._yt_token(p)
        x = requests.post("https://www.googleapis.com/youtube/v3/comments?part=snippet", timeout=30,
                          headers={"Authorization": f"Bearer {tok}"},
                          json={"snippet": {"parentId": r["comment_id"], "textOriginal": r["text"]}})
    elif r["platform"] == "instagram":
        x = requests.post(f"{G()}/{r['comment_id']}/replies", timeout=30,
                          data={"message": r["text"], "access_token": secret(p, "META_PAGE_TOKEN")})
    else:
        x = requests.post(f"{G()}/{r['comment_id']}/comments", timeout=30,
                          data={"message": r["text"], "access_token": secret(p, "META_PAGE_TOKEN")})
    if x.status_code >= 400:
        raise RuntimeError(f"{x.status_code}: {x.text[:300]}")
    return x.json().get("id", "")


def reply() -> int:
    todo = _load("replies.json", [])
    done = _load("replied.json", {})
    left, failed = [], 0
    for i, r in enumerate(todo):
        if r["comment_id"] in done:
            continue
        if i >= MAX_REPLIES_PER_RUN:
            left.append(r)
            continue
        try:
            rid = _post_reply(r)
            done[r["comment_id"]] = {"platform": r["platform"], "reply_id": rid, "text": r["text"],
                                     "at": datetime.now(IST).isoformat(timespec="minutes")}
            print("replied", r["platform"], r["comment_id"])
        except Exception as e:
            failed += 1
            r["error"] = str(e)[:300]
            r["tries"] = r.get("tries", 0) + 1
            if r["tries"] < 3:
                left.append(r)
            print("reply failed", r["platform"], r["comment_id"], e)
    DATA.mkdir(exist_ok=True)
    (DATA / "replies.json").write_text(json.dumps(left, indent=2, ensure_ascii=False))
    (DATA / "replied.json").write_text(json.dumps(done, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    {"collect": collect, "reply": reply}[sys.argv[1]]()
