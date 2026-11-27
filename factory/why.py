"""Why did a video do well? Per platform (owner 2026-11-27).

Called by factory/analyze.py after every metrics pull. For each platform it works out:

1. DRIVERS: which of that platform's own signals move with its views (rank correlation over all
   videos 24 h+ old). Each platform rewards different things: Facebook seems to push what people
   keep watching for 10+ s, Instagram what isn't skipped AND gets sent, YouTube what gets liked /
   found. The data decides, not us.
2. HITS and WHY: a hit is a video with 2x+ the platform's median views (top quarter). For each hit
   we list the signals where it beat the platform's median clearly, and the content features
   (from the job file: how line 1 opens, title style, bucket, length...) it shares with other hits.
3. RECOMMENDATIONS: from 1 and 2, plain changes to try on THAT platform's version. They are only
   ideas until they run as a test (data/tests.json) and the automatic check (factory/experiments.py)
   keeps or rolls them back.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = {"youtube": "YouTube", "instagram": "Instagram", "facebook": "Facebook"}

# signal -> (label, higher is better?)
SIGNALS = {
    "youtube": {"watch_s": ("seconds watched", True), "watch_pct": ("% of the video watched", True),
                "likes_per_1k": ("likes per 1k views", True), "comments_per_1k": ("comments per 1k", True),
                "yt_src_shorts_pct": ("% of views from the Shorts feed", True),
                "yt_src_search_pct": ("% of views from search", True),
                "yt_ret_10": ("% still watching at 10%", True), "yt_ret_end": ("% still watching at the end", True),
                "engaged_pct": ("engaged views %", True)},
    "instagram": {"skip_pct": ("skip rate (first 3 s)", False), "watch_s": ("seconds watched", True),
                  "shares_per_1k": ("shares per 1k views", True), "saves_per_1k": ("saves per 1k views", True),
                  "likes_per_1k": ("likes per 1k views", True), "profile_per_1k": ("profile visits per 1k", True)},
    "facebook": {"watch_s": ("seconds watched", True), "fb_ret_10": ("% still watching at 10%", True),
                 "fb_ret_50": ("% still watching at half way", True), "likes_per_1k": ("likes per 1k views", True),
                 "replays_per_1k": ("replays per 1k views", True)},
}

# Signals that are a RESULT of distribution, not something a script can aim at: they explain, they don't instruct.
OUTCOMES = {"yt_src_shorts_pct", "yt_src_search_pct"}

FEATURES = {
    "opener_you": "line 1 talks to the viewer about something THEY do or have seen ('You've been...', 'You've seen these...')",
    "opener_question": "line 1 is a direct Why/How/What question",
    "opener_claim": "line 1 is a bold claim or myth-bust ('X is NOT...', '...wrong your whole life')",
    "title_plain_question": "title is a plain searchable question ('Why do airplane windows have holes?')",
    "title_claim": "title carries a twist in CAPS ('NOT a shoe cleaner', 'They started WHITE')",
    "myth": "busts a common belief (the video says what people wrongly think)",
    "car_or_home": "about a car part or a household object people own",
    "short": "under 50 s",
}


def _f(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _en(x):
    return x.get("en") if isinstance(x, dict) and "en" in x else x


def job_features(vid: str) -> dict:
    """Simple yes/no content features from the job file of a video id (curious-...-en)."""
    base = re.sub(r"-(en|hi)$", "", vid)
    f = ROOT / "jobs" / "curious" / f"{base}.json"
    if not f.exists():
        return {}
    try:
        j = json.loads(f.read_text())
    except Exception:
        return {}
    sc = j.get("scenes") or [{}]
    line1 = str(_en(sc[0].get("narration")) or "").replace("*", "")
    yt = _en(j.get("youtube")) or {}
    title = str(_en(yt.get("title")) or "")
    said = " ".join(str(_en(s.get("narration")) or "") for s in sc).lower()
    hay = (title + " " + line1 + " " + " ".join(str(_en(s.get("visual")) or "") for s in sc[:2])).lower()
    return {
        "opener_you": bool(re.match(r"^(you('ve|'re| have| are)?|your|next time you|check|look)\b", line1.strip().lower()))
                      or bool(re.search(r"\byou've (seen|been|noticed)\b", line1.lower())),
        "opener_question": bool(re.match(r"^(why|how|what)\b", line1.strip().lower())),
        "opener_claim": bool(re.search(r"\b(not|wrong|isn't|aren't|never)\b", line1.lower())) and "?" not in line1,
        "title_plain_question": bool(re.match(r"^(why|how|what)\b", title.lower())) and not re.search(r"\b[A-Z]{3,}\b", title.replace("#shorts", "")),
        "title_claim": bool(re.search(r"\b[A-Z]{3,}\b", title.replace("#shorts", ""))),
        "myth": bool(re.search(r"\b(myth|most people think|you'd think|isn't|not (a|for|just|dye)|wrong)\b", said)),
        "car_or_home": bool(re.search(r"\b(car|tyre|tire|fuel|window|mirror|fog light|key|lock|toilet|flush|iron|"
                                      r"microwave|toothpaste|cooker|fridge|kettle|door|bath)\b", hay)),
        "short": (j.get("_duration") or 0) < 50 if j.get("_duration") else None,
    }


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 8:
        return None, len(pairs)
    ra, rb = _rank([p[0] for p in pairs]), _rank([p[1] for p in pairs])
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va, vb = math.sqrt(sum((x - ma) ** 2 for x in ra)), math.sqrt(sum((y - mb) ** 2 for y in rb))
    return (round(cov / (va * vb), 2) if va and vb else None), len(pairs)


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def per_platform_rows(live: list[dict], name: str, last_rows: dict) -> list[dict]:
    """One row per video with this platform's views and signals. last_rows[(id, platform)] = the
    newest history.csv row (for the extra why-signals analyze.py doesn't carry)."""
    out = []
    for v in live:
        p = v["platforms"].get(name)
        if not p or not p.get("views") or v["hours"] < 24:
            continue
        raw = last_rows.get((v["id"], name), {})
        views = p["v72"] or p["views"]
        per1k = lambda x: round(1000 * x / p["views"], 1) if x is not None and p["views"] else None  # noqa: E731
        ev = _f(raw.get("yt_engaged_views"))
        row = {"id": v["id"], "date": v["date"], "hook": v["hook"], "bucket": v["bucket"], "views": views,
               "duration": v["yt_duration"] if name == "youtube" else v["duration"],
               "watch_s": p["watch_s"], "watch_pct": p["watch_pct"], "skip_pct": p.get("skip_pct"),
               "likes_per_1k": per1k(p.get("likes")), "comments_per_1k": per1k(p.get("comments")),
               "shares_per_1k": per1k(p.get("shares")), "saves_per_1k": per1k(p.get("saved")),
               "profile_per_1k": per1k(_f(raw.get("profile_visits"))),
               "replays_per_1k": per1k(_f(raw.get("replays"))),
               "engaged_pct": round(100 * ev / p["views"], 1) if ev is not None and p["views"] else None}
        for k in ("yt_src_shorts_pct", "yt_src_search_pct", "yt_ret_10", "yt_ret_end", "fb_ret_10", "fb_ret_50"):
            row[k] = _f(raw.get(k))
        feats = job_features(v["id"])
        if feats.get("short") is None:
            feats["short"] = (row["duration"] or 99) < 50
        row["features"] = feats
        out.append(row)
    return out


def review(name: str, rows: list[dict]) -> dict:
    sig = SIGNALS[name]
    med_views = _median([r["views"] for r in rows])
    res = {"videos": len(rows), "median_views": med_views, "drivers": [], "hits": [], "recommendations": []}
    if len(rows) < 8 or not med_views:
        res["recommendations"].append(f"Not enough {NAME[name]} videos 24 h+ old yet to say why (need 8).")
        return res
    logv = [math.log10(max(r["views"], 1)) for r in rows]
    for k, (label, up) in sig.items():
        rho, n = spearman([r.get(k) for r in rows], logv)
        if rho is None:
            continue
        good = rho if up else -rho  # positive = "more of the good direction goes with more views"
        res["drivers"].append({"signal": k, "label": label, "rho": rho, "n": n, "strength": round(good, 2)})
    res["drivers"].sort(key=lambda d: -d["strength"])
    meds = {k: _median([r.get(k) for r in rows]) for k in sig}
    ranked = sorted(rows, key=lambda r: -r["views"])
    hits = [r for r in ranked[:max(1, len(rows) // 4)] if r["views"] >= 2 * med_views]
    rest = [r for r in rows if r not in hits]
    for h in hits:
        why = []
        for k, (label, up) in sig.items():
            a, m = h.get(k), meds.get(k)
            if a is None or m in (None, 0):
                continue
            if (up and a >= 1.25 * m) or (not up and a <= 0.8 * m):
                why.append(f"{label} {a:g} vs {m:g} typical")
        feats = [FEATURES[f] for f, on in h["features"].items() if on and f in FEATURES]
        res["hits"].append({"id": h["id"], "hook": h["hook"], "views": h["views"], "signals": why, "features": feats})
    # content features over-represented in hits / in the bottom half
    feat_lines, avoid_lines = [], []
    bottom = ranked[len(ranked) // 2:]
    if len(hits) >= 2:
        for f, desc in FEATURES.items():
            hr = sum(1 for h in hits if h["features"].get(f)) / len(hits)
            rr = sum(1 for r in rest if r["features"].get(f)) / max(1, len(rest))
            if hr >= 0.6 and hr >= rr + 0.3:
                feat_lines.append((f, desc, hr, rr))
            br = sum(1 for r in bottom if r["features"].get(f)) / max(1, len(bottom))
            tr = sum(1 for r in ranked[:len(ranked) // 2] if r["features"].get(f)) / max(1, len(ranked) // 2)
            if br >= tr + 0.35:
                avoid_lines.append((f, desc, br, tr))
    res["features_in_hits"] = [{"feature": f, "hits": round(hr, 2), "others": round(rr, 2)} for f, _, hr, rr in feat_lines]
    # recommendations
    strong = [d for d in res["drivers"] if d["strength"] >= 0.4]
    for d in [d for d in strong if d["signal"] in OUTCOMES][:1]:
        res["recommendations"].append(
            f"{NAME[name]} reach depends on the platform's own feed picking the video up ({d['label']} goes with views, "
            f"rank correlation {d['rho']:+.2f}); videos it drops end up living off search. So the lever is what the feed "
            f"judges in the first seconds (the next point), not the title or tags.")
    for d in [d for d in strong if d["signal"] not in OUTCOMES][:2]:
        k, (label, up) = d["signal"], sig[d["signal"]]
        hv = [h.get(k) for h in hits if h.get(k) is not None]
        rv = [r.get(k) for r in rows if r not in hits and r.get(k) is not None]
        if hv and rv:
            hm, rm = _median(hv), _median(rv)
            if (up and hm <= rm) or (not up and hm >= rm):
                continue  # goes with views overall, but the hits weren't better on it: no target
            res["recommendations"].append(
                f"{NAME[name]} reach follows {label} (rank correlation {d['rho']:+.2f} over {d['n']} videos): its hits "
                f"had a median {hm:g} vs {rm:g} for the rest. Aim each {NAME[name]} version at {hm:g}+"
                + ("" if up else " or less") + ".")
    for d in []:
        vals = []
        if vals:
            target = min(vals) if up else max(vals)
            res["recommendations"].append(
                f"{NAME[name]} reach follows {label} (rank correlation {d['rho']:+.2f} over {d['n']} videos). Every "
                f"{NAME[name]} hit had {label} {'at least' if up else 'at most'} {target:g} (typical {meds[k]:g}). "
                f"Aim each {NAME[name]} version at that.")
    for f, desc, hr, rr in feat_lines:
        res["recommendations"].append(f"{NAME[name]} hits share this: {desc} ({hr:.0%} of hits vs {rr:.0%} of the rest). Do more of it on {NAME[name]}.")
    for f, desc, br, tr in avoid_lines:
        res["recommendations"].append(f"{NAME[name]}: the weaker half leans on this: {desc} ({br:.0%} vs {tr:.0%} of the better half). Use less of it on {NAME[name]}.")
    if not res["recommendations"]:
        res["recommendations"].append(f"No clear {NAME[name]} pattern yet: no signal tracks reach strongly (all |rho| < 0.4).")
    return res


def report_lines(name: str, r: dict) -> list[str]:
    L = [f"#### Why it works on {NAME[name]}", ""]
    if r["drivers"]:
        L.append("- What moves with views here (rank correlation, + = more of it, more views): "
                 + "; ".join(f"{d['label']} {d['rho']:+.2f}" for d in r["drivers"][:5]))
    for h in r["hits"]:
        L.append(f"- Hit: {h['hook']} ({h['views']:,.0f}). Why: " + ("; ".join(h["signals"]) or "no signal stands out")
                 + (". Content: " + "; ".join(h["features"]) if h["features"] else ""))
    L += [f"- **Recommendation:** {x}" for x in r["recommendations"]]
    return L
