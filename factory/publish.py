"""Post every rendered video whose time has come, on each platform not yet posted.

    python -m factory.publish            # post what's due now
    python -m factory.publish --force ID # post one job right away

Safe to re-run: a platform that already has a post id is skipped, so a retry
never double-posts.
"""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import channels, platforms

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
IST = timezone(timedelta(hours=5, minutes=30))


def load_states() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(STATE.glob("*.json"))]


def save_state(s: dict) -> None:
    STATE.mkdir(exist_ok=True)
    (STATE / f"{s['id']}.json").write_text(json.dumps(s, indent=2))


def is_due(s: dict, now: datetime) -> bool:
    if not s.get("publish"):
        return False
    when = datetime.fromisoformat(f"{s['date']}T{s.get('slot', '19:00')}").replace(tzinfo=IST)
    # Allow up to 3 days late (e.g. a missed run), never earlier than the slot.
    return when - timedelta(minutes=20) <= now <= when + timedelta(days=3)


def fetch_video(s: dict) -> tuple[Path, dict]:
    out = ROOT / "out" / s["id"]
    if not (out / "final.mp4").exists():
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run(["gh", "release", "download", s["release"], "--dir", str(out), "--clobber"], check=True)
    return out / "final.mp4", json.loads((out / "meta.json").read_text())


def prefix(s: dict) -> str:
    return channels.load(s["channel"])["secret_prefix"]


def publish(s: dict) -> dict:
    video, meta = fetch_video(s)
    p = prefix(s)
    s.setdefault("platforms", {})
    s.setdefault("errors", {})
    for name in platforms.enabled_platforms(p):
        if name in s["platforms"]:
            continue
        try:
            print(f"[{s['channel']}/{s['id']}] posting to {name}", flush=True)
            res = platforms.UPLOADERS[name](p, video, meta)
            res["posted_at"] = datetime.now(IST).isoformat(timespec="minutes")
            s["platforms"][name] = res
            s["errors"].pop(name, None)
            print(f"  ok: {res.get('url')}")
        except Exception as e:  # keep going with the other platforms
            s["errors"][name] = f"{type(e).__name__}: {e}"[:500]
            traceback.print_exc()
        save_state(s)
    return s


def main(argv: list[str]) -> int:
    now = datetime.now(IST)
    states = load_states()
    if len(argv) > 2 and argv[1] == "--force":
        states = [s for s in states if s["id"] == argv[2]]
        for s in states:
            s["publish"] = True
    else:
        states = [s for s in states if is_due(s, now)]
    failed = False
    for s in states:
        if set(platforms.enabled_platforms(prefix(s))) - set(s.get("platforms", {})):
            s = publish(s)
            failed |= bool(s.get("errors"))
    if not states:
        print("Nothing due.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
