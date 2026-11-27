"""Keep what works, roll back what doesn't: automatically (owner 2026-11-27).

    python -m factory.experiments          # apply verdicts from metrics/insights.json
    python -m factory.experiments --dry    # say what would happen, change nothing

Runs after every metrics pull + numbers review (metrics.yml). Every change to how we make
videos is a test in data/tests.json:

    {"id", "change", "platforms": [...], "started", "videos": 5, "status": "running",
     "switch": [{"file": "channels/curious-en/channel.json", "path": "youtube_cut.on", "off": false}],
     "rollback": "plain words for anything a switch can't undo (prompt/playbook lines)"}

factory/analyze.py judges each running test per platform (views lift vs the 7 videos before,
divided by the lift on platforms the test doesn't touch, plus guard rails, plus an early harm
stop). Here we act on the verdict:
- "keep": status "kept". The change stays.
- "revert": every switch is set to its "off" value right away (so the next render is already
  back to before), status "reverted", and if the test has a "rollback" text, "needs_undo": true
  so the next script run undoes the prompt/playbook lines and clears it.
Either way the result is written on the test and Prashant gets one alert.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IST = timezone(timedelta(hours=5, minutes=30))
TESTS = ROOT / "data" / "tests.json"


def _set(obj: dict, path: str, value) -> object:
    keys = path.split(".")
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    old = obj.get(keys[-1])
    obj[keys[-1]] = value
    return old


def flip_off(switches: list[dict], dry: bool = False) -> list[str]:
    done = []
    for sw in switches or []:
        f = ROOT / sw["file"]
        data = json.loads(f.read_text())
        old = _set(data, sw["path"], sw["off"])
        done.append(f"{sw['file']} {sw['path']}: {old!r} -> {sw['off']!r}")
        if not dry:
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return done


def main(argv: list[str]) -> int:
    dry = "--dry" in argv
    ins = json.loads((ROOT / "metrics" / "insights.json").read_text())
    verdicts = {t["id"]: t for t in ins.get("tests") or []}
    data = json.loads(TESTS.read_text())
    today = datetime.now(IST).date().isoformat()
    changed, alerts = False, []
    for t in data["tests"]:
        if t.get("status") != "running":
            continue
        v = verdicts.get(t["id"]) or {}
        verdict, why = v.get("verdict"), v.get("why", "")
        if verdict not in ("keep", "revert"):
            continue
        t["ended"], t["result"] = today, why
        if verdict == "keep":
            t["status"] = "kept"
            alerts.append(f"KEPT {t['id']}: it works. {why}. Change: {t['change']}")
        else:
            t["status"] = "reverted"
            flipped = flip_off(t.get("switch"), dry)
            t["rolled_back"] = flipped
            if t.get("rollback"):
                t["needs_undo"] = True
            alerts.append(f"ROLLED BACK {t['id']}: it didn't work. {why}. Undone: "
                          + ("; ".join(flipped) or "nothing switchable")
                          + (f". The next script run also undoes: {t['rollback']}" if t.get("rollback") else ""))
        changed = True
    for a in alerts:
        print(a)
    if changed and not dry:
        TESTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        from . import notify
        for a in alerts:
            notify.main("info", f"Test result: {a.split(':', 1)[0]}", a)
    if not alerts:
        print("No test verdicts to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
