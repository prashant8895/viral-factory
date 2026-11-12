"""Daily quiz + shoutouts (since 2026-11-13).

Every Curious video ends with a quick guess about TOMORROW's topic ("quiz" in the job).
The next video answers it, and at render time we read the comments on yesterday's video
(YouTube, Instagram, Facebook), find the first people (max 3) who got it right, and show
their names on a short "shoutout" scene. Names are shown, never spoken (the voice would
mangle handles).

    python -m factory.quiz check <job.json>   # dry run: who would get the shoutout right now
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_NAMES = 3
# names we never put on screen (spam, slurs, sexual, links); kept short on purpose: anything
# that smells off is skipped, the next fastest person gets the spot instead
_BAD = re.compile(r"(https?:|www\.|\.com|sex|porn|nude|xxx|fuck|shit|bitch|dick|cock|pussy|boob|onlyfans|"
                  r"crypto|forex|bitcoin|telegram|whatsapp|promo|follow4|f4f|nazi|hitler|rape)", re.I)


def _when(s: str | None) -> datetime:
    if not s:
        return datetime.max.replace(tzinfo=timezone.utc)
    s = s.replace("Z", "+00:00")
    s = re.sub(r"([+-]\d\d)(\d\d)$", r"\1:\2", s)
    return datetime.fromisoformat(s)


def is_correct(text: str, quiz: dict) -> bool:
    """A comment counts when it clearly picks the right option: by letter ("B", "option b",
    "b)", "answer is b") or by the option's words, and never names a wrong option too."""
    t = re.sub(r"[^\w\s()]", " ", (text or "").lower()).strip()
    opts = {k.lower(): v for k, v in (quiz.get("options") or {}).items()}
    ans = str(quiz["answer"]).lower()
    letters = set()
    if t in opts:  # the whole comment is just "b"
        letters.add(t)
    for m in re.finditer(r"(?:option|answer is|answer|ans|its|it s|it's)\s*\(?([a-d])\)?(?![\w])|\(([a-d])\)|(?:^|\s)([a-d])\)",
                         t):
        letters.add(next(g for g in m.groups() if g))
    letters &= set(opts)
    if letters:
        return letters == {ans}
    kw = {k.lower(): [w.lower() for w in v] for k, v in (quiz.get("keywords") or {}).items()}
    for k, v in opts.items():  # the option's own words count too
        kw.setdefault(k, []).extend(w for w in re.findall(r"[a-z]{4,}", str(v).lower()))
    words = set(re.findall(r"[a-z0-9']+", t))
    hit = lambda k: any((w in words) if " " not in w else (w in t) for w in kw.get(k, []))  # noqa: E731
    return hit(ans) and not any(hit(k) for k in kw if k != ans)


def display_name(author: str | None, platform: str) -> str | None:
    """@handle for YouTube/Instagram, 'First L.' for Facebook (real names: keep it light)."""
    a = (author or "").strip()
    if not a or _BAD.search(a):
        return None
    if platform == "facebook":
        parts = a.split()
        a = parts[0] + (f" {parts[-1][0]}." if len(parts) > 1 else "")
    else:
        a = "@" + a.lstrip("@")
    return a if len(a) <= 24 else a[:23] + "…"


def previous(job: dict) -> dict | None:
    """The last posted video on this page before this one, if it asked a quiz."""
    from .publish import load_states
    me = job.get("id", "")
    page = job.get("channel")
    best = None
    for s in load_states():
        if s.get("channel") != page or s.get("id") == me or not s.get("platforms") or not s.get("quiz"):
            continue
        if str(s.get("date") or "") > str(job.get("date") or "9999"):
            continue
        if best is None or (s.get("date"), s.get("slot")) > (best.get("date"), best.get("slot")):
            best = s
    # only if that quiz really was the last thing posted (a later video without a quiz resets it)
    for s in load_states():
        if (s.get("channel") == page and s.get("platforms") and s.get("id") != me and best
                and (s.get("date"), s.get("slot")) > (best.get("date"), best.get("slot"))
                and str(s.get("date")) <= str(job.get("date") or "9999")):
            return None
    return best


def winners(state: dict) -> list[dict]:
    from . import comments
    from .publish import prefix
    quiz, rows = state["quiz"], []
    for name, post in (state.get("platforms") or {}).items():
        if name not in comments.READERS:
            continue
        try:
            for c in comments.READERS[name](prefix(state), post["id"]):
                c["platform"] = name
                rows.append(c)
        except Exception as e:  # one platform down never blocks the video
            print(f"[shoutout] could not read {name} comments: {str(e)[:120]}")
    rows.sort(key=lambda c: _when(c.get("time")))
    out, seen = [], set()
    for c in rows:
        if not is_correct(c.get("text", ""), quiz):
            continue
        n = display_name(c.get("author"), c["platform"])
        key = re.sub(r"[^a-z0-9]", "", (n or "").lower())
        if not n or key in seen:
            continue
        seen.add(key)
        out.append({"name": n, "platform": c["platform"], "time": c.get("time"), "comment_id": c.get("comment_id")})
        if len(out) >= MAX_NAMES:
            break
    return out


def apply(job: dict) -> dict:
    """Fill (or drop) the job's shoutout scene. Returns what was decided, for the state file."""
    idx = [i for i, s in enumerate(job["scenes"]) if s.get("shoutout")]
    if not idx:
        return {}
    i = idx[0]
    sc = job["scenes"][i]
    prev = None
    try:
        prev = previous(job)
        won = winners(prev) if prev else []
    except Exception as e:
        print(f"[shoutout] skipped: {str(e)[:160]}")
        won = []
    if not prev:
        print("[shoutout] yesterday's video asked no quiz: scene dropped")
        job["scenes"].pop(i)
        return {}
    q = prev["quiz"]
    params = {**sc.get("anim_params", {}), "names": [w["name"] for w in won], "answer": q["answer"],
              "answer_text": (q.get("options") or {}).get(q["answer"], "")}
    if won:
        print(f"[shoutout] {len(won)} name(s): " + ", ".join(w["name"] for w in won))
    elif sc.get("narration_none"):
        print("[shoutout] nobody got it right yet: using narration_none")
        sc["narration"] = sc["narration_none"]
    else:
        job["scenes"].pop(i)
        return {"from": prev["id"], "names": []}
    sc["anim"] = sc.get("anim") or "anims/shoutout.html"
    sc["anim_params"] = params
    return {"from": prev["id"], "names": won}


if __name__ == "__main__" and sys.argv[1:2] == ["check"]:
    j = json.loads(Path(sys.argv[2]).read_text())
    j["channel"] = j.get("channel", "curious") + ("-en" if j.get("languages") else "")
    j["id"] = j["id"] + ("-en" if j.get("languages") else "")
    p = previous(j)
    print("previous quiz video:", p and p["id"])
    print(json.dumps(winners(p) if p else [], indent=2, ensure_ascii=False))
