"""Daily numbers review: turns metrics/history.csv + state/ into a plain report and
machine-readable insights that the morning ideas and the script writer must read.

    python -m factory.analyze            # writes metrics/report.md and metrics/insights.json

Runs right after every metrics pull (metrics.yml), so the feedback loop is:
post -> metrics -> analyze -> insights.json -> next pitches/scripts -> post.

What it measures, per video (all platforms added up, AND each platform on its own since
2026-11-27: every rule and test verdict is also given per platform):
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
            "yt_duration": _f((st.get("youtube_cut") or {}).get("duration")) or dur,
            "yt_cut": bool(st.get("youtube_cut")),
            "ig_cut": bool(st.get("instagram_cut")),
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


PNAME = {"youtube": "YouTube", "instagram": "Instagram", "facebook": "Facebook"}


def _band(d) -> str:
    d = d or 0
    return "<40s" if d < 40 else "40-50s" if d <= 50 else "50-70s" if d <= 70 else "70s+"


def _on(v: dict, name: str) -> dict | None:
    """One video as seen on one platform only (owner 2026-11-27: judge every platform on its own
    numbers; what works on Facebook may not work on YouTube). None if it has no numbers there."""
    p = v["platforms"].get(name)
    if not p or p.get("views") is None:
        return None
    short = (name == "youtube" and v["yt_cut"]) or (name == "instagram" and v.get("ig_cut"))
    dur = v["yt_duration"] if short else v["duration"]
    return {**{k: v[k] for k in ("id", "date", "hook", "bucket", "hook_style", "picture_style", "voice",
                                  "tests", "hours", "yt_cut")},
            "duration": dur, "length_band": _band(dur), "cut": "short cut" if short else "full video",
            "views": p["views"], "v24": p["v24"], "v72": p["v72"], "watch_pct": p["watch_pct"],
            "watch_s": p["watch_s"], "ig_watch_s": p["watch_s"], "skip_pct": p.get("skip_pct"),
            "shares_per_1k": round(1000 * p["shares"] / p["views"], 1) if p.get("shares") is not None and p["views"] else None}


def _lean_rules(vids: list[dict], keys: tuple) -> list[str]:
    """'Lean towards' rules from groups of 3+ videos that lead on both median and average views."""
    groups = {k: _group(vids, k) for k in keys}
    wins: dict[frozenset, list] = {}  # leads won by the very same set of videos changed together: report once
    for key in keys:
        trusted = [g for g in groups[key] if g["trusted"] and g["median_views"]]
        if len(trusted) < 2:
            continue
        best, worst = trusted[0], trusted[-1]
        if best["median_views"] >= 1.25 * worst["median_views"] and (best["mean_views"] or 0) >= 1.25 * (worst["mean_views"] or 1):
            ids = frozenset(v["id"] for v in vids if str(v[key]) == best["group"])
            wins.setdefault(ids, []).append((key, best, worst))
    rules = []
    for ids, ws in wins.items():
        key, best, worst = ws[0]
        if len(ws) == 1:
            rules.append(f"{key}: '{best['group']}' beats '{worst['group']}' ({_fmt(best['median_views'])} vs "
                         f"{_fmt(worst['median_views'])} median views, {best['n']} vs {worst['n']} videos).")
        else:
            dates = sorted(v["date"] for v in vids if v["id"] in ids)
            rules.append(f"The {len(ids)} videos of {dates[0]} to {dates[-1]} lead ({_fmt(best['median_views'])} vs "
                         f"{_fmt(worst['median_views'])} median views), but they were {', '.join(repr(w[1]['group']) for w in ws)} "
                         f"all at once ({', '.join(w[0] for w in ws)}), so we can't tell which one did it.")
    return rules


def platform_review(live: list[dict], name: str) -> dict:
    vids = [x for x in (_on(v, name) for v in live) if x]
    ripe = [v for v in vids if v["hours"] >= 24]
    ranked = sorted(ripe, key=lambda v: -(v["v72"] or v["views"]))
    recent = [v for v in vids if v["hours"] >= 24][-5:]
    before = [v for v in vids if v["hours"] >= 24][-12:-5]
    out = {"videos": len(vids), "total_views": sum(v["views"] for v in vids),
           "median_views": _median([v["v72"] or v["views"] for v in ripe]),
           "median_watch_s": _median([v["watch_s"] for v in vids]),
           "median_watch_pct": _median([v["watch_pct"] for v in vids]),
           "last5_median": _median([v["v72"] or v["views"] for v in recent]),
           "prev7_median": _median([v["v72"] or v["views"] for v in before]),
           "top": [f"{v['hook']} ({_fmt(v['v72'] or v['views'])})" for v in ranked[:3]],
           "bottom": [f"{v['hook']} ({_fmt(v['v72'] or v['views'])})" for v in ranked[-3:]] if len(ranked) > 3 else [],
           "rules": _lean_rules(vids, ("bucket", "hook_style", "picture_style", "voice", "length_band", "cut")),
           "groups": {k: _group(vids, k) for k in ("bucket", "length_band", "cut")}}
    a, b = out["last5_median"], out["prev7_median"]
    if a is not None and b and (a < 0.7 * b or a > 1.3 * b):
        out["rules"].insert(0, f"{PNAME[name]} is {'DOWN' if a < b else 'UP'}: last 5 videos median "
                               f"{_fmt(a)} views vs {_fmt(b)} for the 7 before them.")
    return out


def _test_on(t: dict, live: list[dict], name: str) -> dict:
    """One test on one platform: tagged videos vs the 7 videos (72 h old) before it started.
    Views (the main measure), seconds watched, and skip rate (Instagram) or watch % (YouTube,
    Facebook) as guard rails. Early numbers (24 h) feed the harm stop."""
    vids = [x for x in (_on(v, name) for v in live) if x]
    need, tid = int(t.get("videos", 5)), t["id"]
    tagged = [v for v in vids if tid in v["tests"]]
    ripe = [v for v in tagged if v["hours"] >= 72][:need]
    early = [v for v in tagged if v["hours"] >= 24]
    before = [v for v in vids if (v["date"] or "") < t.get("started", "") and v["hours"] >= 72][-7:]
    third = "skip_pct" if name == "instagram" else "watch_pct"
    m = lambda vs, k: _median([v[k] for v in vs])  # noqa: E731
    a = {k: m(ripe or tagged, k) for k in ("v72", "watch_s", third)}
    b = {k: m(before, k) for k in ("v72", "watch_s", third)}
    a24, b24 = m(early, "v24"), m(before, "v24")
    return {"test": a, "before": b, "videos_72h": len(ripe), "videos_24h": len(early), "need": need,
            "third": third, "ready": len(ripe) >= need and bool(before),
            "lift": round(a["v72"] / b["v72"], 2) if a["v72"] and b["v72"] else None,
            "lift24": round(a24 / b24, 2) if a24 and b24 and len(early) >= 3 else None,
            "verdict": "waiting"}


WORKS = 1.10   # a change must lift views on its platform by 10%+ (after the control) to be kept
HARM = 0.60    # 3+ videos at 24 h under 60% of before (after the control) = stop early
GUARD = 0.85   # and seconds watched / skip / watch % may not get more than 15% worse


def judge_test(t: dict, by: dict, control: dict) -> tuple[str, str]:
    """Keep only what WORKS, roll back the rest (owner 2026-11-27).

    Each platform is judged against its OWN videos before the test started. The untouched
    platforms are shown for context only, not divided out: our numbers show the platforms move
    independently (Facebook went 24x on two videos that did nothing on YouTube), so one platform
    is no fair control for another. Noise is handled by the 5-video median and the 10% bar."""
    ctrl_lifts = [r["lift"] for r in control.values() if r.get("lift")]
    ctrl = ctrl24 = 1.0
    why, works, harm = [], 0, False
    for n, r in by.items():
        if r.get("lift24") is not None and r["lift24"] / ctrl24 < HARM:
            harm = True
            why.append(f"{PNAME[n]} 24 h views {r['lift24']:.0%} of before: harm stop")
    if harm and t.get("status") == "running":
        return "revert", "; ".join(why)
    if not all(r["ready"] for r in by.values()):
        return "waiting", ""
    for n, r in by.items():
        a, b, third = r["test"], r["before"], r["third"]
        adj = (r["lift"] or 0) / ctrl
        guard_ok = all(
            a[k] is None or b[k] is None or (a[k] >= GUARD * b[k] if k != "skip_pct" else a[k] <= b[k] / GUARD)
            for k in ("watch_s", third))
        ok = adj >= WORKS and guard_ok
        works += ok
        r["adj_lift"], r["verdict"] = round(adj, 2), "keep" if ok else "revert"
        why.append(f"{PNAME[n]} views x{adj:.2f} vs before" + (f" (untouched platforms x{_median(ctrl_lifts):.2f}, context only)" if ctrl_lifts else "")
                   + ("" if guard_ok else ", watch/skip got worse") + (": works" if ok else ": doesn't work"))
    verdict = "keep" if works * 2 >= len(by) and all(r.get("adj_lift", 0) >= 0.8 for r in by.values()) else "revert"
    return verdict, "; ".join(why)


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
        # Verdict per platform (owner 2026-11-27): keep only what works, roll back the rest.
        # A test scoped to some platforms is judged only there, with the others as control.
        scope = t.get("platforms") or list(MAIN)
        res["platforms"] = scope
        res["by_platform"] = {n: _test_on(t, live, n) for n in scope}
        control = {n: _test_on(t, live, n) for n in MAIN if n not in scope}
        verdict, why_line = judge_test(t, res["by_platform"], control)
        if t.get("status") == "running":
            res["verdict"], res["why"] = verdict, why_line
        tests_out.append(res)
    running = [t for t in tlist if t.get("status") == "running"]
    for n in MAIN:  # max 2 tests touching one platform at once, or we can't tell which change did what
        here = [t["id"] for t in running if n in (t.get("platforms") or MAIN)]
        if len(here) > 2:
            flags.append(f"{len(here)} tests running on {PNAME[n]} at once ({', '.join(here)}): max is 2 per platform.")
    reviews = {n: platform_review(live, n) for n in MAIN}
    # Why each platform's hits worked + what to do on that platform (factory/why.py)
    from . import why
    hist = OUT / "history.csv"
    newest: dict = {}
    for r in (csv.DictReader(hist.open()) if hist.exists() else []):
        newest[(r["id"], r["platform"])] = r
    for n in MAIN:
        reviews[n]["why"] = why.review(n, why.per_platform_rows(live, n, newest))
        for x in reviews[n]["why"]["recommendations"]:
            rules.append(f"Recommendation for {PNAME[n]}: {x}")
    for key in ("length_band", "bucket"):  # where the platforms want different things, say so plainly
        bests = {}
        for n in MAIN:
            gs = [g for g in reviews[n]["groups"][key] if g["trusted"] and g["median_views"]]
            if len(gs) >= 2:
                bests[n] = gs[0]["group"]
        if len(set(bests.values())) > 1:
            rules.append(f"{key}: the platforms disagree (" + ", ".join(f"{PNAME[n]} best: '{g}'" for n, g in bests.items())
                         + "). Don't follow the all-platform rule blindly: YouTube has its own cut, so tune that cut "
                         "for YouTube and the full video for Instagram and Facebook.")
    for n in MAIN:
        r = reviews[n]
        for line in r["rules"]:
            rules.append(f"{PNAME[n]} only: {line}")
        if r["top"]:
            rules.append(f"{PNAME[n]} best: " + "; ".join(r["top"]) + (f". Weakest: " + "; ".join(r["bottom"]) if r["bottom"] else "") + ".")
    for t in tests_out:
        if t["status"] == "running":
            rules.append(f"Test '{t['id']}' ({t['change']}): {t['videos_made']}/{t['needed']} videos, "
                         f"{t['videos_72h']} at 72 h, verdict: {t['verdict']}.")

    insights = {"updated": now.isoformat(timespec="minutes"), "videos": len(live),
                "total_views": sum(v["views"] for v in live), "platform_views": plat_tot,
                "median_watch_pct": wp, "median_shares_per_1k": sp,
                "median_ig_watch_s": igs, "median_yt_watch_s": yts,
                "rules": rules, "flags": flags, "groups": groups, "by_platform": reviews, "voice_trial": vt, "tests": tests_out,
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
    L += ["## Each platform on its own", "",
          "Judge every change per platform: a format can win on Facebook and lose on YouTube. YouTube gets its "
          "own shorter cut (playbook \"YouTube cut\"); Instagram and Facebook get the full video.", "",
          "| Platform | Videos | Total views | Median views (72 h) | Last 5 / 7 before | Sec watched | Watch % |",
          "|---|---|---|---|---|---|---|"]
    for n in MAIN:
        r = reviews[n]
        L.append(f"| {PNAME[n]} | {r['videos']} | {_fmt(r['total_views'])} | {_fmt(r['median_views'])} | "
                 f"{_fmt(r['last5_median'])} / {_fmt(r['prev7_median'])} | {_fmt(r['median_watch_s'], ' s')} | {_fmt(r['median_watch_pct'], '%')} |")
    for n in MAIN:
        r = reviews[n]
        L += ["", f"### {PNAME[n]}", ""] + [f"- {x}" for x in r["rules"] or ["No trusted difference yet (need 3+ videos per group)."]]
        if r["top"]:
            L.append("- Best: " + "; ".join(r["top"]))
        if r["bottom"]:
            L.append("- Weakest: " + "; ".join(r["bottom"]))
        L += [""] + why.report_lines(n, r["why"]) + [""]
        for key in ("length_band", "bucket", "cut"):
            gs = r["groups"][key]
            if len(gs) > 1:
                L.append(f"- By {key.replace('_', ' ')}: " + "; ".join(f"{g['group']} {_fmt(g['median_views'])} median views, "
                         f"{_fmt(g['median_watch_pct'], '%')} watched ({g['n']}{'' if g['trusted'] else ', too few'})" for g in gs))
    L += ["", "## What to do next", ""] + [f"- {r}" for r in rules or ["Not enough videos yet for trusted rules (need 3+ per group)."]]
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
        L += ["", "Per platform (72 h views, seconds watched, IG skip or watch %; test / before):", ""]
        for t in tests_out:
            if t["status"] != "running":
                continue
            parts = []
            for n, r in t["by_platform"].items():
                a, b = r["test"], r["before"]
                third = "skip_pct" if n == "instagram" else "watch_pct"
                parts.append(f"{PNAME[n]} {_fmt(a['v72'])}/{_fmt(b['v72'])} views, {_fmt(a['watch_s'], ' s')}/{_fmt(b['watch_s'], ' s')}, "
                             f"{_fmt(a[third], '%')}/{_fmt(b[third], '%')}: **{r['verdict']}**")
            L.append(f"- {t['id']}: " + "; ".join(parts))
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
