"""YouTube search: make the channel findable by its name.

    python -m factory.yt_seo            # read only: writes data/youtube_channel.json
    python -m factory.yt_seo apply      # also updates the channel About text + keywords,
                                        # and backfills the brand line/tags on posted Shorts

What it changes (settings in channels/curious-en/channel.json -> "youtube_brand"):
  - channel About text, channel keywords, default language, country
  - every posted English Short: the brand name in the description, brand tags,
    default (audio) language "en"  (titles are never touched)
New uploads get the same through platforms.youtube_upload -> brand_snippet.
The channel name and @handle can't be changed by the API: the report prints them so
Prashant can fix them in YouTube Studio if they don't contain the brand name.
Never prints a key.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

from . import platforms
from .channels import load

ROOT = Path(__file__).resolve().parent.parent
PAGE = "curious-en"
API = "https://www.googleapis.com/youtube/v3"


def brand() -> dict:
    return load(PAGE).get("youtube_brand") or {}


def brand_snippet(sn: dict, b: dict | None = None) -> dict:
    """Adds the brand line, brand tags and language to a video snippet (idempotent)."""
    b = b if b is not None else brand()
    if not b:
        return sn
    sn = dict(sn)
    name, line = b["name"], b["video_line"]
    desc = sn.get("description") or ""
    if name.lower() not in desc.lower():
        lines = desc.rstrip().split("\n")
        # keep the hashtag line last (YouTube shows the hashtags above the title)
        if lines and lines[-1].lstrip().startswith("#"):
            desc = "\n".join(lines[:-1]).rstrip() + "\n\n" + line + "\n" + lines[-1]
        else:
            desc = desc.rstrip() + "\n\n" + line
    sn["description"] = desc[:5000]
    tags = list(dict.fromkeys(list(b.get("video_tags") or []) + list(sn.get("tags") or [])))
    out, total = [], 0  # YouTube caps tags at 500 characters in all
    for t in tags:
        if total + len(t) + 1 > 480:
            break
        out.append(t)
        total += len(t) + 1
    sn["tags"] = out
    sn["defaultLanguage"] = b.get("language", "en")
    sn["defaultAudioLanguage"] = b.get("language", "en")
    return sn


def _keywords(words: list[str]) -> str:
    return " ".join(f'"{w}"' if " " in w else w for w in words)[:500]


def main(apply: bool) -> None:
    p = load(PAGE)["secret_prefix"]
    b = brand()
    tok = platforms._yt_token(p)
    H = {"Authorization": f"Bearer {tok}"}
    r = requests.get(f"{API}/channels", params={"part": "snippet,brandingSettings,statistics,status", "mine": "true"},
                     headers=H, timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        sys.exit("Signed in, but there's no YouTube channel on this login")
    ch = items[0]
    sn, bs = ch["snippet"], ch.get("brandingSettings", {})
    report = {
        "title": sn.get("title"), "handle": sn.get("customUrl"),
        "subscribers": ch.get("statistics", {}).get("subscriberCount"),
        "videos": ch.get("statistics", {}).get("videoCount"),
        "made_for_kids": ch.get("status", {}).get("madeForKids"),
        "before": {"description": sn.get("description"), "keywords": bs.get("channel", {}).get("keywords"),
                   "country": bs.get("channel", {}).get("country"),
                   "language": bs.get("channel", {}).get("defaultLanguage")},
        "advice": [],
    }
    norm = lambda s: "".join(c for c in (s or "").lower() if c.isalnum())
    if norm(b["name"]) not in norm(sn.get("title")):
        report["advice"].append(f"Channel name '{sn.get('title')}' doesn't contain '{b['name']}': rename it in YouTube Studio > Customisation > Basic info.")
    if norm(b["name"]) not in norm(sn.get("customUrl")):
        report["advice"].append(f"Handle {sn.get('customUrl')} doesn't contain '{b['name']}': pick e.g. @ohthatswhy... in Studio > Customisation > Basic info.")
    print(f"Channel: {report['title']}  handle: {report['handle']}  subs: {report['subscribers']}  videos: {report['videos']}")

    if apply:
        chan = dict(bs.get("channel", {}))
        chan.update({"description": b["channel_description"], "keywords": _keywords(b["channel_keywords"]),
                     "defaultLanguage": b.get("language", "en"), "country": b.get("country", "IN")})
        body = {"id": ch["id"], "brandingSettings": {**bs, "channel": chan}}
        body["brandingSettings"].pop("hints", None)
        u = requests.put(f"{API}/channels", params={"part": "brandingSettings"}, headers=H, json=body, timeout=30)
        report["channel_update"] = "ok" if u.ok else f"failed {u.status_code}: {u.text[:300]}"
        print("channel About + keywords:", report["channel_update"])

        ids = []
        for f in sorted((ROOT / "state").glob("curious-*-en.json")):
            yt = (json.loads(f.read_text()).get("platforms") or {}).get("youtube") or {}
            if yt.get("id"):
                ids.append(yt["id"])
        report["videos_updated"], report["videos_failed"] = [], {}
        for i in range(0, len(ids), 50):
            got = requests.get(f"{API}/videos", params={"part": "snippet", "id": ",".join(ids[i:i + 50])},
                               headers=H, timeout=30)
            got.raise_for_status()
            for it in got.json().get("items", []):
                old = it["snippet"]
                keep = {k: old[k] for k in ("title", "description", "tags", "categoryId",
                                            "defaultLanguage", "defaultAudioLanguage") if k in old}
                new = brand_snippet(keep, b)
                if new == keep:
                    continue
                up = requests.put(f"{API}/videos", params={"part": "snippet"}, headers=H,
                                  json={"id": it["id"], "snippet": new}, timeout=30)
                if up.ok:
                    report["videos_updated"].append(it["id"])
                else:
                    report["videos_failed"][it["id"]] = f"{up.status_code}: {up.text[:200]}"
        print(f"videos updated: {len(report['videos_updated'])}, failed: {len(report['videos_failed'])}")

    for a in report["advice"]:
        print("ADVICE:", a)
    out = ROOT / "data" / "youtube_channel.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if apply and (report.get("channel_update") != "ok" or report.get("videos_failed")):
        sys.exit(1)


if __name__ == "__main__":
    main(apply=len(sys.argv) > 1 and sys.argv[1] == "apply")
