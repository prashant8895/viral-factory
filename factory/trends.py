"""What people are searching and watching right now. Free; runs daily before the morning ideas.

Writes data/trends.json:
  searches  - YouTube/Google autocomplete for curiosity openers (what people type), EN + Hindi
  daily     - Google's daily trending searches (India, US)
  shorts    - this week's most-viewed English curiosity Shorts in the US, UK and India (title, views, channel)
  hashtags  - hashtags those Shorts use, weighted by views (pick only the ones that fit the video)
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from . import platforms

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "trends.json"
UA = {"User-Agent": "Mozilla/5.0 (video-factory trends)"}

SEEDS = {
    "en": ["why do", "why is there a", "why are", "why does", "what is the purpose of", "what is the hole in",
           "what is the little", "why do they put", "how does a", "is it true that"],
    "hi": ["kyu hota hai", "kyon hota hai", "kya hota hai", "ka kya kaam hai", "kaise kaam karta hai",
           "kyu lagate hai", "क्यों होता है", "क्यों लगाते हैं"],
}
SHORTS_QUERIES = {"en": ["why", "did you know", "facts you didn't know"]}  # Hindi paused 2026-11-12
# 2026-11-23 (owner): the page is global now, so trends come from the US and UK as well as India.
SHORTS_REGIONS = ("US", "GB", "IN")
SUGGEST_GL = {"en": ("us", "gb", "in"), "hi": ("in",)}


def suggest(q: str, lang: str, yt: bool, gl: str = "in") -> list[str]:
    params = {"client": "firefox", "hl": lang, "gl": gl, "q": q}
    if yt:
        params["ds"] = "yt"
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search", params=params, headers=UA, timeout=20)
        return [s for s in r.json()[1] if s.strip().lower() != q.lower()]
    except Exception as e:
        print("suggest failed", q, e)
        return []


def daily(geo: str) -> list[dict]:
    try:
        r = requests.get("https://trends.google.com/trending/rss", params={"geo": geo}, headers=UA, timeout=20)
        root = ET.fromstring(r.content)
        ns = {"ht": "https://trends.google.com/trending/rss"}
        return [{"title": i.findtext("title"), "traffic": i.findtext("ht:approx_traffic", namespaces=ns)}
                for i in root.iter("item")][:20]
    except Exception as e:
        print("daily trends failed", geo, e)
        return []


def shorts(prefix: str) -> tuple[list[dict], Counter]:
    tok = platforms._yt_token(prefix)
    h = {"Authorization": f"Bearer {tok}"}
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    vids, tags = [], Counter()
    seen: set[str] = set()
    for lang, qs in SHORTS_QUERIES.items():
        for q, region in ((q, rg) for q in qs for rg in SHORTS_REGIONS):
            r = requests.get("https://www.googleapis.com/youtube/v3/search", headers=h, timeout=30, params={
                "part": "id", "q": q, "type": "video", "videoDuration": "short", "order": "viewCount",
                "publishedAfter": since, "regionCode": region, "relevanceLanguage": lang, "maxResults": 25})
            ids = [i["id"]["videoId"] for i in r.json().get("items", []) if i["id"]["videoId"] not in seen]
            seen.update(ids)
            if not ids:
                continue
            v = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=h, timeout=30, params={
                "part": "snippet,statistics", "id": ",".join(ids)}).json().get("items", [])
            for it in v:
                sn, st = it["snippet"], it.get("statistics", {})
                views = int(st.get("viewCount", 0))
                vids.append({"lang": lang, "query": q, "region": region, "title": sn["title"], "channel": sn["channelTitle"],
                             "views": views, "id": it["id"]})
                text = sn.get("title", "") + " " + sn.get("description", "") + " " + " ".join(
                    "#" + t.replace(" ", "") for t in sn.get("tags", []))
                for tag in set(t.lower() for t in re.findall(r"#\w+", text)):
                    tags[tag] += max(views, 1)
    vids.sort(key=lambda x: -x["views"])
    return vids[:40], tags


def main() -> None:
    out = {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "searches": {}, "daily": {}}
    for lang, seeds in SEEDS.items():
        found = []
        for s in seeds:
            for gl in SUGGEST_GL.get(lang, ("in",)):
                found += suggest(s, "hi" if lang == "hi" else "en", yt=True, gl=gl)
                found += suggest(s, "hi" if lang == "hi" else "en", yt=False, gl=gl)
        out["searches"][lang] = list(dict.fromkeys(found))[:120]
    for geo in ("US", "GB", "IN"):
        out["daily"][geo] = daily(geo)
    try:
        vids, tags = shorts("CURIOUS_EN_")
        out["shorts"] = vids
        out["hashtags"] = [{"tag": t, "weight": w} for t, w in tags.most_common(40)]
    except Exception as e:
        print("shorts failed", e)
        out["shorts"], out["hashtags"] = [], []
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in out.items()})


if __name__ == "__main__":
    main()
