"""Daily numbers review: turns metrics/history.csv + state/ into a plain report and
machine-readable insights that the morning ideas and the script writer must read.

    python -m factory.analyze            # writes metrics/report.md and metrics/insights.json

Runs right after every metrics pull (metrics.yml), so the feedback loop is:
post -> metrics -> analyze -> insights.json -> next pitches/scripts -> post.

What it measures, per video (all platforms of one page added up):
- views at ~24 h and ~72 h (closest check to that age), and latest
- watch %: Instagram average watch time / video length (YouTube too, once the
  analytics scope is on the token)
- seconds actually watched (Instagram, YouTube): the fair hold measure when video length changes
- likes, shares, saves per 1,000 views (share rate is the strongest "send it to a friend" signal)
- how late it went out versus its slot (late posts get fewer first-hour views)
Then compares groups (bucket, hook style, length band, picture style, voice) and lists
what to do more / less of. Groups with fewer than 3 videos are shown but not trusted; a
"lean towards" rule needs the lead in BOTH median and average views, and groupings that split
the videos the same way (changed together) are reported once as "can't tell apart".
Approved Morning Slate changes are tracked as tests (data/tests.json) and get a keep/revert
verdict once enough tagged videos are 72 h old.
"""
from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "metrics"
IST = timezone(timedelta(hours=5, minutes=30))
MAIN = ("youtube", "instagram", "facebook")


def _f(v) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def _views(row: dict) -> float | None:
    if row["platform"] == "facebook":
        return _f(row.get("blue_reels_play_count")) or _f(row.get("views"))
    return _f(row.get("views"))


def _at_age(rows: list[dict], hours: float, slack: float) -> float | None:
    """Views at the check closest to `hours` old (within slack), else None."""
    best = None
    for r in rows:
        h, v = _f(r.get("hours_live")), _views(r)
        if h is None or v is None or abs(h - hours) > slack:
            continue
        if best is None or abs(h - hours) < abs(best[0] - hours):
            best = (h, v)
    return best[1] if best else None


def _late_minutes(state: dict) -> float | None:
    times = [p.get("posted_at") for k, p in (state.get("platforms") or {}).items() if k in MAIN]
    times = [datetime.fromisoformat(t) for t in times if t]
    if not times or not state.get("date"):
        return None
    slot = datetime.fromisoformat(f"{state['date']}T{state.get('slot', '19:00')}").replace(tzinfo=IST)
    return round((min(times) - slot).total_seconds() / 60)


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def collect() -> list[dict]:
    hist = OUT / "history.csv"
    rows = list(csv.DictReader(hist.open())) if hist.exists() else []
    states = {p.stem: json.loads(p.read_text()) for p in (ROOT / "state").glob("*.json")}
    by_vid: dict[str, list[dict]] = {}
    for r in rows:
        by_vid.setdefault(r["id"], []).append(r)
    videos = []
    for vid, vrows in by_vid.items():
        st = states.get(vid, {})
        if st.get("taken_down") and not st.get("publish"):
            continue  # a broken upload we removed; its numbers would mislead
        dur = _f(st.get("duration"))
        plat = {}
        for name in MAIN:
            pr = sorted([r for r in vrows if r["platform"] == name], key=lambda r: _f(r["hours_live"]) or 0)
            if not pr:
                continue
            last = pr[-1]
            avg_ms = _f(last.get("ig_reels_avg_watch_time")) or _f(last.get("post_video_avg_time_watched"))
            avg_s = (avg_ms / 1000 if avg_ms and avg_ms > 300 else avg_ms) if avg_ms else None
            yt_pct = _f(last.get("yt_avg_view_pct"))
            watch_s = _f(last.get("yt_avg_view_sec")) if name == "youtube" else avg_s
            plat[name] = {
                "v24": _at_age(pr, 24, 12), "v72": _at_age(pr, 72, 30), "views": _views(last),
                "hours": _f(last["hours_live"]), "likes": _f(last.get("likes")),
                "shares": _f(last.get("shares")), "saved": _f(last.get("saved")),
                "comments": _f(last.get("comments")),
                "watch_pct": yt_pct if yt_pct is not None else (round(100 * avg_s / dur, 1) if avg_s and dur else None),
                "watch_s": round(watch_s, 1) if watch_s else None,
                "skip_pct": _f(last.get("reels_skip_rate")), "follows": _f(last.get("follows")),
                "error": last.get("error") or last.get("fb_insights_error") or None,
            }
        if not plat:
            continue
        tot = lambda k: sum(p[k] or 0 for p in plat.values()) if any(p[k] is not None for p in plat.values()) else None
        views = tot("views") or 0
        likes = tot("likes")
        # shares only come from Instagram, so rate them against the views of platforms that report them
        sh = [(p["shares"], p["views"]) for p in plat.values() if p["shares"] is not None and p["views"]]
        shares_rate = round(1000 * sum(a for a, _ in sh) / sum(b for _, b in sh), 1) if sh else None
        hours = max(p["hours"] or 0 for p in plat.values())
        videos.append({
            "id": vid, "channel": st.get("channel") or vrows[-1]["channel"], "date": st.get("date"),
            "bucket": st.get("bucket") or vrows[-1].get("bucket"), "hook": (st.get("hook_text") or "").replace("*", ""),
            "hook_style": st.get("hook_style") or vrows[-1].get("hook_style") or "none",
            "duration": dur, "slot": st.get("slot"), "late_min": _late_minutes(st),
            "picture_style": st.get("picture_style", "photo"), "voice": st.get("voice", "kokoro"),
            "hours": hours, "views": views, "v24": tot("v24"), "v72": tot("v72"),
            "likes_per_1k": round(1000 * likes / views, 1) if likes is not None and views else None,
            "shares_per_1k": shares_rate,
            "watch_pct": _median([p["watch_pct"] for p in plat.values()]),
            "skip_pct": (plat.get("instagram") or {}).get("skip_pct"),
            "ig_watch_s": (plat.get("instagram") or {}).get("watch_s"),
            "yt_watch_s": (plat.get("youtube") or {}).get("watch_s"),
            "tests": st.get("tests") or [],
            "follows": tot("follows"),
            "platforms": plat,
            "yt_pct_seen": any(_f(r.get("yt_avg_view_pct")) is not None for r in vrows),
        })
    return sorted(videos, key=lambda v: v["date"] or "")


def _group(videos, key):
    g: dict[str, list] = {}
    for v in videos:
        g.setdefault(str(v[key]), []).append(v)
    out = []
    for k, vs in g.items():
        out.append({"group": k, "n": len(vs), "trusted": len(vs) >= 3,
                    "median_v24": _median([v["v24"] for v in vs]),
                    "median_views": _median([v["views"] for v in vs]),
                    "mean_views": round(statistics.mean([v["views"] for v in vs])) if vs else None,
                    "median_ig_watch_s": _median([v["ig_watch_s"] for v in vs]),
                    "median_watch_pct": _median([v["watch_pct"] for v in vs]),
                    "median_shares_per_1k": _median([v["shares_per_1k"] for v in vs])})
    return sorted(out, key=lambda x: -(x["median_views"] or 0))


def _fmt(x, suffix=""):
    return "–" if x is None else (f"{x:,.0f}{suffix}" if abs(x) >= 10 or x == int(x) else f"{x:.1f}{suffix}")


def main() -> None:
    now = datetime.now(IST)
    all_videos = collect()
    live = [v for v in all_videos if v["channel"] == "curious-en"]  # Hindi paused 2026-11-12
    if not live:
        print("no English videos with numbers yet")
        return
    groups = {k: _group(live, k) for k in ("bucket", "hook_style", "picture_style", "voice")}
    for v in live:
        d = v["duration"] or 0
        v["length_band"] = "<40s" if d < 40 else "40-50s" if d <= 50 else "50-70s" if d <= 70 else "70s+"
    groups["length_band"] = _group(live, "length_band")

    ranked = sorted([v for v in live if v["hours"] >= 24], key=lambda v: -(v["v72"] or v["views"]))
    top, bottom = ranked[:3], ranked[-3:] if len(ranked) > 3 else []
    plat_tot = {n: sum((v["platforms"].get(n, {}).get("views") or 0) for v in live) for n in MAIN}

    flags = []
    late = [v for v in live if v["late_min"] is not None and abs(v["late_min"]) > 30]
    if late:
        flags.append(f"{len(late)} of {len(live)} videos went out more than 30 min off their slot: "
                     + ", ".join(f"{v['id'][8:-3]} ({v['late_min']:+.0f} min)" for v in late[-5:]))
    fb_noinsights = [v for v in live if "read_insights" in str((v["platforms"].get("facebook") or {}).get("error"))]
    if fb_noinsights:
        flags.append("Facebook watch time is missing: the Meta page token lacks read_insights. Make a new token "
                     "with tools/get_meta_ids.py (the permission list is at the top) and update CURIOUS_EN_META_PAGE_TOKEN.")
    if not any(v.get("yt_pct_seen") for v in live):
        flags.append("YouTube watch % is missing: in Google Cloud (the project of YT_CLIENT_ID) enable "
                     "'YouTube Analytics API', then re-run tools/get_youtube_token.py once (it now asks for "
                     "yt-analytics.readonly) and update CURIOUS_EN_YT_REFRESH_TOKEN.")
    dead = [v for v in live if v["hours"] >= 12 and v["views"] < 50]
    if dead:
        flags.append("Under 50 views after 12 h+: " + ", ".join(v["id"][8:-3] for v in dead))

    # Plain rules the next pitches/scripts must follow. Only from groups with 3+ videos.
    rules = []
    # Groupings that split the videos exactly the same way changed together: one comparison, not three rules.
    seen: dict[frozenset, list[str]] = {}
    for key in groups:
        split = frozenset(frozenset(v["id"] for v in live if str(v[key]) == g["group"]) for g in groups[key])
        seen.setdefault(split, []).append(key)
    for keys in seen.values():
        key, gs = keys[0], groups[keys[0]]
        trusted = [g for g in gs if g["trusted"] and g["median_views"]]
        if len(trusted) < 2:
            continue
        best, worst = trusted[0], trusted[-1]
        med_lead = best["median_views"] >= 1.25 * worst["median_views"]
        mean_lead = (best["mean_views"] or 0) >= 1.25 * (worst["mean_views"] or 1)
        together = (f" ({', '.join(keys)} all changed together, so we can't tell which one did it)"
                    if len(keys) > 1 else "")
        if med_lead and mean_lead:
            rules.append(f"{key}: '{best['group']}' beats '{worst['group']}' "
                         f"({_fmt(best['median_views'])} vs {_fmt(worst['median_views'])} median views, "
                         f"{_fmt(best['mean_views'])} vs {_fmt(worst['mean_views'])} average, "
                         f"{best['n']} vs {worst['n']} videos). Lean towards '{best['group']}'{together}.")
        elif med_lead:
            rules.append(f"{key}: '{best['group']}' leads on median views ({_fmt(best['median_views'])} vs "
                         f"{_fmt(worst['median_views'])}) but not on average ({_fmt(best['mean_views'])} vs "
                         f"{_fmt(worst['mean_views'])}): it lifts the weak videos, not the hits. No change yet{together}.")
    wp = _median([v["watch_pct"] for v in live])
    igs, yts = _median([v["ig_watch_s"] for v in live]), _median([v["yt_watch_s"] for v in live])
    if igs is not None:
        rules.append(f"People watch a median {igs:.0f} s on Instagram" + (f" and {yts:.0f} s on YouTube" if yts else "")
                     + " whatever the video's length. The first real answer must land inside those first "
                     f"{igs:.0f} s; judge hold by seconds watched and skip rate, not watch % (watch % drops "
                     "on its own when videos get longer). Length itself is set by the playbook, not by this rule.")
    sp = _median([v["shares_per_1k"] for v in live])
    skip = _median([v["skip_pct"] for v in live])
    if skip is not None and skip > 50:
        rules.append(f"Instagram skip rate is {skip:.0f}%: most people swipe away in the first 3 s. The opening "
                     "picture + 'Ever wondered why' line must show the thing itself, big and clear, from frame 1.")
    if top:
        rules.append("Top videos so far: " + "; ".join(f"{v['hook']} ({v['bucket']}, {_fmt(v['v72'] or v['views'])} views)" for v in top)
                     + ". Pitch more topics like these.")
    if bottom:
        rules.append("Weakest: " + "; ".join(f"{v['hook']} ({v['bucket']}, {_fmt(v['v72'] or v['views'])})" for v in bottom)
                     + ". Avoid these angles unless a new twist.")

    # Voice trial: Prashant's cloned voice for N videos, judged against every other English video.
    trial = json.loads((ROOT / "channels" / "curious-en" / "channel.json").read_text()).get("voice_trial") or {}
    vt = None
    if trial:
        name, need = trial.get("name", "clone"), int(trial.get("videos", 5))
        tv = [v for v in live if v["voice"] == name]
        base = [v for v in live if v["voice"] != name and v["hours"] >= 72]
        ripe = [v for v in tv if v["hours"] >= 72][:need]
        m = lambda vs, k: _median([v[k] for v in vs])
        vt = {"status": trial.get("status"), "videos_made": len(tv), "videos_72h": len(ripe), "needed": need,
              "trial": {k: m(ripe or tv, k) for k in ("v72", "watch_pct", "skip_pct")},
              "baseline": {k: m(base, k) for k in ("v72", "watch_pct", "skip_pct")}, "verdict": "waiting"}
        if len(ripe) >= need and base:
            t, b = vt["trial"], vt["baseline"]
            wins = sum([
                t["v72"] is not None and b["v72"] is not None and t["v72"] >= 0.9 * b["v72"],
                t["watch_pct"] is not None and b["watch_pct"] is not None and t["watch_pct"] >= 0.9 * b["watch_pct"],
                t["skip_pct"] is not None and b["skip_pct"] is not None and t["skip_pct"] <= 1.1 * b["skip_pct"],
            ])
            vt["verdict"] = "keep" if wins >= 2 else "revert"
            vt["why"] = (f"{wins} of 3 checks held up (views at 72 h, watch %, Instagram skip; each within 10% "
                         f"of the {len(base)} other videos)")
        rules.append(f"Voice trial ({name}): {len(tv)}/{need} videos made, {len(ripe)} at 72 h, verdict: {vt['verdict']}.")

    # Tests: every approved Morning Slate change, judged against the videos before it started.
    tests_out = []
    tfile = ROOT / "data" / "tests.json"
    tlist = json.loads(tfile.read_text()).get("tests", []) if tfile.exists() else []
    for t in tlist:
        tid, need = t["id"], int(t.get("videos", 5))
        tagged = [v for v in live if tid in v["tests"]]
        before = [v for v in live if (v["date"] or "") < t.get("started", "") and v["hours"] >= 72][-7:]
        ripe = [v for v in tagged if v["hours"] >= 72][:need]
        m = lambda vs, k: _median([v[k] for v in vs])
        res = {"id": tid, "change": t.get("change"), "kind": t.get("kind"), "started": t.get("started"),
               "status": t.get("status"), "videos_made": len(tagged), "videos_72h": len(ripe), "needed": need,
               "test": {k: m(ripe or tagged, k) for k in ("v72", "ig_watch_s", "skip_pct")},
               "before": {k: m(before, k) for k in ("v72", "ig_watch_s", "skip_pct")}, "verdict": "waiting"}
        if t.get("status") == "running" and len(ripe) >= need and before:
            a, b = res["test"], res["before"]
            wins = sum([
                a["v72"] is not None and b["v72"] is not None and a["v72"] >= 0.9 * b["v72"],
                a["ig_watch_s"] is not None and b["ig_watch_s"] is not None and a["ig_watch_s"] >= 0.9 * b["ig_watch_s"],
                a["skip_pct"] is not None and b["skip_pct"] is not None and a["skip_pct"] <= 1.1 * b["skip_pct"],
            ])
            res["verdict"] = "keep" if wins >= 2 else "revert"
            res["why"] = (f"{wins} of 3 checks held up (views at 72 h, Instagram seconds watched, Instagram skip; "
                          f"each within 10% of the {len(before)} videos before it)")
        tests_out.append(res)
    running = [t for t in tlist if t.get("status") == "running"]
    if len(running) > 2:
        flags.append(f"{len(running)} tests running at once ({', '.join(t['id'] for t in running)}): "
                     "max is 2, or we can't tell which change did what.")
    for t in tests_out:
        if t["status"] == "running":
            rules.append(f"Test '{t['id']}' ({t['change']}): {t['videos_made']}/{t['needed']} videos, "
                         f"{t['videos_72h']} at 72 h, verdict: {t['verdict']}.")

    insights = {"updated": now.isoformat(timespec="minutes"), "videos": len(live),
                "total_views": sum(v["views"] for v in live), "platform_views": plat_tot,
                "median_watch_pct": wp, "median_shares_per_1k": sp,
                "median_ig_watch_s": igs, "median_yt_watch_s": yts,
                "rules": rules, "flags": flags, "groups": groups, "voice_trial": vt, "tests": tests_out,
                "top": [v["id"] for v in top], "bottom": [v["id"] for v in bottom],
                "per_video": [{k: v[k] for k in ("id", "date", "bucket", "hook", "hook_style", "duration", "late_min",
                                                 "views", "v24", "v72", "watch_pct", "skip_pct", "follows",
                                                 "likes_per_1k", "shares_per_1k", "ig_watch_s", "yt_watch_s", "tests")}
                              | {f"{n}_watch_pct": v["platforms"].get(n, {}).get("watch_pct") for n in MAIN}
                              for v in live]}
    (OUT / "insights.json").write_text(json.dumps(insights, indent=2, ensure_ascii=False))

    hi = [v for v in all_videos if v["channel"] == "curious-hi"]
    L = [f"# Oh That's Why: numbers review", "",
         f"Updated {now:%d %b %Y, %H:%M} IST. English page, {len(live)} videos, "
         f"{_fmt(insights['total_views'])} views in total "
         f"(YouTube {_fmt(plat_tot['youtube'])}, Instagram {_fmt(plat_tot['instagram'])}, Facebook {_fmt(plat_tot['facebook'])}). "
         f"Median watch {_fmt(wp, '%')} ({_fmt(igs, ' s')} on Instagram, {_fmt(yts, ' s')} on YouTube), "
         f"median shares {_fmt(sp)} per 1k views.", ""]
    if hi:
        L += [f"Hindi page (paused 12 Nov): {len(hi)} videos, {_fmt(sum(v['views'] for v in hi))} views in total.", ""]
    L += ["## What to do next", ""] + [f"- {r}" for r in rules or ["Not enough videos yet for trusted rules (need 3+ per group)."]]
    if flags:
        L += ["", "## Problems in the data or posting", ""] + [f"- {f}" for f in flags]
    L += ["", "## Every video", "",
          "| Date | Hook | Bucket | Hook style | Len | Late | 24 h | 72 h | Now | Watch YT / IG / FB | Sec watched IG / YT | IG skip | Shares/1k | Follows | Views YT | IG | FB |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in reversed(live):
        p = v["platforms"]
        L.append(f"| {v['date']} | {(v['hook'] or '').replace('*', '')} | {v['bucket']} | {v['hook_style']} | "
                 f"{_fmt(v['duration'], 's')} | {_fmt(v['late_min'], 'm')} | {_fmt(v['v24'])} | {_fmt(v['v72'])} | "
                 f"{_fmt(v['views'])} | " + " / ".join(_fmt(p.get(n, {}).get("watch_pct"), "%") for n in MAIN)
                 + f" | {_fmt(v['ig_watch_s'], ' s')} / {_fmt(v['yt_watch_s'], ' s')}"
                 + f" | {_fmt(v['skip_pct'], '%')} | {_fmt(v['shares_per_1k'])} | {_fmt(v['follows'])} | "
                 + " | ".join(_fmt(p.get(n, {}).get("views")) for n in MAIN) + " |")
    if vt:
        f = lambda d: f"{_fmt(d['v72'])} views at 72 h, watch {_fmt(d['watch_pct'], '%')}, IG skip {_fmt(d['skip_pct'], '%')}"
        L += ["", "## Voice trial (Prashant's voice)", "",
              f"- Videos: {vt['videos_made']} made, {vt['videos_72h']} of {vt['needed']} old enough to judge (72 h)",
              f"- Your voice (median): {f(vt['trial'])}", f"- Other videos (median): {f(vt['baseline'])}",
              f"- Verdict: **{vt['verdict']}**" + (f" ({vt['why']})" if vt.get("why") else "")]
    if tests_out:
        L += ["", "## Tests (approved changes)", "",
              "| Test | Change | Started | Videos (72 h) | 72 h views test / before | IG sec test / before | IG skip test / before | Verdict |",
              "|---|---|---|---|---|---|---|---|"]
        for t in tests_out:
            a, b = t["test"], t["before"]
            L.append(f"| {t['id']} | {t['change']} | {t['started']} | {t['videos_made']} ({t['videos_72h']}/{t['needed']}) | "
                     f"{_fmt(a['v72'])} / {_fmt(b['v72'])} | {_fmt(a['ig_watch_s'], ' s')} / {_fmt(b['ig_watch_s'], ' s')} | "
                     f"{_fmt(a['skip_pct'], '%')} / {_fmt(b['skip_pct'], '%')} | {t['status'] if t['status'] != 'running' else t['verdict']} |")
    for key, gs in groups.items():
        L += ["", f"## By {key.replace('_', ' ')}", "", "| Group | Videos | Median 24 h | Median views | Average views | Watch | IG sec | Shares/1k |",
              "|---|---|---|---|---|---|---|---|"]
        for g in gs:
            L.append(f"| {g['group']}{'' if g['trusted'] else ' (too few)'} | {g['n']} | {_fmt(g['median_v24'])} | "
                     f"{_fmt(g['median_views'])} | {_fmt(g['mean_views'])} | {_fmt(g['median_watch_pct'], '%')} | "
                     f"{_fmt(g['median_ig_watch_s'], ' s')} | {_fmt(g['median_shares_per_1k'])} |")
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
