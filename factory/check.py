"""Connection check: signs in to every connected platform and prints the account name.
Posts nothing, changes nothing. Never prints a key.

    python -m factory.check
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

from . import platforms
from .channels import secret

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["curious-en", "curious-hi"]


def _yt(p: str) -> str:
    tok = platforms._yt_token(p)
    r = requests.get("https://www.googleapis.com/youtube/v3/channels",
                     params={"part": "snippet", "mine": "true"},
                     headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    return items[0]["snippet"]["title"] if items else "signed in, but no channel on this login"


def _meta(p: str, what: str) -> str:
    base = f"https://graph.facebook.com/{platforms.GRAPH}"
    tok = secret(p, "META_PAGE_TOKEN")
    if what == "instagram":
        r = requests.get(f"{base}/{secret(p, 'IG_USER_ID')}", params={"fields": "username", "access_token": tok}, timeout=30)
        r.raise_for_status()
        return "@" + r.json()["username"]
    r = requests.get(f"{base}/{secret(p, 'FB_PAGE_ID')}", params={"fields": "name", "access_token": tok}, timeout=30)
    r.raise_for_status()
    return r.json()["name"]


def main() -> int:
    bad = 0
    for page in PAGES:
        p = json.loads((ROOT / "channels" / page / "channel.json").read_text())["secret_prefix"]
        on = platforms.enabled_platforms(p)
        tok = secret(p, "META_PAGE_TOKEN")
        if tok and "facebook" not in on:  # print the Page id so Facebook can be switched on later
            try:
                me = requests.get(f"https://graph.facebook.com/{platforms.GRAPH}/me",
                                  params={"fields": "id,name", "access_token": tok}, timeout=30).json()
                print(f"{page:11} facebook   page id for {p}FB_PAGE_ID: {me.get('id')} ({me.get('name')})")
            except Exception as e:
                print(f"{page:11} facebook   could not read page id: {str(e)[:100]}")
        for name in ("youtube", "instagram", "facebook"):
            if name not in on:
                print(f"{page:11} {name:10} not set up yet")
                continue
            try:
                who = _yt(p) if name == "youtube" else _meta(p, name)
                print(f"{page:11} {name:10} OK -> {who}")
            except Exception as e:  # say what failed without echoing any key
                msg = str(e)
                for k in ("YT_CLIENT_SECRET", "YT_REFRESH_TOKEN", "META_PAGE_TOKEN"):
                    v = secret(p, k)
                    if v:
                        msg = msg.replace(v, "***")
                print(f"{page:11} {name:10} FAILED: {msg[:200]}")
                bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
