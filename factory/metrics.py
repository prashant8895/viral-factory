"""Pull views, likes, shares etc. for recent posts into metrics/.

Claude reads metrics/latest.json every morning before pitching, and
metrics/history.csv every Sunday for the weekly learnings.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta

from . import platforms
from .publish import IST, ROOT, load_states, prefix

OUT = ROOT / "metrics"


def main() -> None:
    now = datetime.now(IST)
    OUT.mkdir(exist_ok=True)
    rows = []
    states = [s for s in load_states() if s.get("platforms")]
    yt = {}
    for key in {s["channel"] for s in states}:
        ids = [s["platforms"]["youtube"]["id"] for s in states if s["channel"] == key and "youtube" in s["platforms"]]
        try:
            yt.update(platforms.youtube_stats(prefix({"channel": key}), ids))
        except Exception as e:
            print(f"YouTube stats failed for {key}:", e)

    for s in states:
        for name, post in s["platforms"].items():
            posted = datetime.fromisoformat(post["posted_at"])
            hours = round((now - posted).total_seconds() / 3600, 1)
            if hours > 24 * 30:
                continue
            try:
                p = prefix(s)
                if name == "youtube":
                    st = yt.get(post["id"], {})
                elif name == "instagram":
                    st = platforms.instagram_stats(p, post["id"])
                else:
                    st = platforms.facebook_stats(p, post["id"])
            except Exception as e:
                st = {"error": str(e)[:200]}
            rows.append({"checked": now.isoformat(timespec="minutes"), "channel": s["channel"], "id": s["id"],
                         "bucket": s.get("bucket"), "hook": s.get("hook_text"), "slot": s.get("slot"),
                         "platform": name, "hours_live": hours, **st})

    (OUT / "latest.json").write_text(json.dumps(rows, indent=2))
    hist = OUT / "history.csv"
    fields = ["checked", "channel", "id", "bucket", "hook", "slot", "platform", "hours_live", "views", "likes",
              "comments", "shares", "saved", "reach", "ig_reels_avg_watch_time", "blue_reels_play_count",
              "post_video_avg_time_watched", "privacy", "error"]
    new = not hist.exists()
    with hist.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows written")


if __name__ == "__main__":
    main()
