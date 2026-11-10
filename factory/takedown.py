"""Take a posted video down from every platform it went to.

    python -m factory.takedown curious-2026-11-10-winter-smog-en [more ids...]

For each id in state/: deletes the YouTube video, the Instagram Reel and Story, and the
Facebook Reel. What was removed (or why a platform refused) is kept in the state file under
"taken_down", the state is set to publish: false so the publisher never posts it again,
and the exit code is 1 if anything could not be removed.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

import requests

from . import platforms
from .publish import IST, STATE, prefix, save_state


def _youtube(p: str, vid: str) -> None:
    r = requests.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": vid},
                        headers={"Authorization": f"Bearer {platforms._yt_token(p)}"}, timeout=60)
    if r.status_code not in (204, 404):
        raise RuntimeError(f"YouTube refused ({r.status_code}): {r.text[:300]}")


def _meta(p: str, obj_id: str) -> None:
    r = requests.delete(f"https://graph.facebook.com/{platforms.GRAPH}/{obj_id}",
                        params={"access_token": platforms._need(p, "META_PAGE_TOKEN")}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Meta refused ({r.status_code}): {r.text[:300]}")


REMOVERS = {"youtube": _youtube, "instagram": _meta, "instagram_story": _meta, "facebook": _meta}


def takedown(job_id: str) -> bool:
    path = STATE / f"{job_id}.json"
    s = json.loads(path.read_text())
    p = prefix(s)
    s["publish"] = False  # never re-post this one
    gone = s.setdefault("taken_down", {})
    left = {}
    for name, post in (s.get("platforms") or {}).items():
        try:
            REMOVERS[name](p, post["id"])
            gone[name] = {**post, "removed_at": datetime.now(IST).isoformat(timespec="minutes")}
            print(f"[{job_id}] removed from {name}: {post.get('url')}", flush=True)
        except Exception as e:  # noqa: BLE001 - try every platform, report all
            left[name] = {**post, "takedown_error": f"{type(e).__name__}: {e}"[:400]}
            print(f"[{job_id}] could NOT remove from {name}: {e}", flush=True)
    s["platforms"] = left
    save_state(s)
    return not left


def main(ids: list[str]) -> int:
    ok = all([takedown(i) for i in ids])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
