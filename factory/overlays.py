"""Code-made motion on top of the pictures (free): poster title, scene headlines,
and labels / arrows / rings / crosses / ticks / counters that pop in on a spoken word.

Everything is drawn as ASS subtitle events, so it costs nothing and needs no extra tools.

In a scene of the job file:
    "headline": "NOT A *SHOE CLEANER*",              # top of screen; *word* = yellow
    "overlays": [
      {"type": "arrow", "x": 0.72, "y": 0.62, "dir": "down", "on": "brush"},
      {"type": "label", "text": "SKIRT BRUSH", "x": 0.5, "y": 0.42, "on": "called"},
      {"type": "ring",  "x": 0.7, "y": 0.6, "r": 0.12, "on": "gap"},
      {"type": "cross", "x": 0.5, "y": 0.55, "on": "not"},
      {"type": "tick",  "x": 0.5, "y": 0.55, "on": "safe"},
      {"type": "counter", "from": 0, "to": 65, "suffix": " CASES", "x": 0.5, "y": 0.4, "on": "65"}
    ]
x and y are 0–1 across the frame. "on" = the overlay appears when that word is spoken
(or "at": seconds into the scene).
"""
from __future__ import annotations

import re

W, H = 1080, 1920
YELLOW, RED, GREEN, WHITE, BLACK = "&H0000E6FF&", "&H003C3CFF&", "&H0050D050&", "&H00FFFFFF&", "&H00000000&"

STYLES = (
    "Style: Poster,Anton,196,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,6,8,50,50,150,1\n"
    "Style: Head,Anton,118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,9,5,8,50,50,170,1\n"
    "Style: Tag,Anton,84,&H00000000,&H00000000,&H0000E6FF,&H0000E6FF,0,0,0,0,100,100,1,0,3,18,0,5,0,0,0,1\n"
    "Style: Shape,Arial,20,&H0000E6FF,&H0000E6FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,7,0,0,0,1\n"
)


def _ts(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _colour_words(text: str, colour: str) -> str:
    """*word* -> coloured word, everything upper-case, braces made safe."""
    text = text.upper().replace("{", "(").replace("}", ")")
    return re.sub(r"\*([^*]+)\*", lambda m: "{\\c" + colour + "}" + m.group(1) + "{\\c" + WHITE + "}", text)


def _two_lines(text: str) -> str:
    """Break a title into two balanced lines (poster look), unless it already has a break."""
    if "\\N" in text or "|" in text:
        return text.replace("|", "\\N")
    words = text.split()
    if len(words) < 3:
        return text
    best, cut = 10**9, 1
    for i in range(1, len(words)):
        d = abs(len(" ".join(words[:i])) - len(" ".join(words[i:])))
        if d < best:
            best, cut = d, i
    return " ".join(words[:cut]) + "\\N" + " ".join(words[cut:])


def poster(hook: str, dur: float = 2.6) -> list[str]:
    """The opening title, like a poster: dark band behind, huge two-colour words."""
    hook = _two_lines(hook)
    band = (f"Dialogue: 0,{_ts(0)},{_ts(dur)},Shape,,0,0,0,,"
            r"{\an7\pos(0,0)\bord0\1c&H000000&\1a&H50&\fad(0,250)\p1}" + f"m 0 0 l {W} 0 {W} 820 0 820{{\\p0}}")
    words = (f"Dialogue: 2,{_ts(0)},{_ts(dur)},Poster,,0,0,0,,"
             r"{\fad(0,250)\fscx60\fscy60\t(0,160,\fscx104\fscy104)\t(160,260,\fscx100\fscy100)}"
             + _colour_words(hook, RED))
    return [band, words]


def headline(text: str, start: float, end: float) -> str:
    return (f"Dialogue: 2,{_ts(start)},{_ts(end)},Head,,0,0,0,,"
            r"{\fad(80,120)\fscx80\fscy80\t(0,140,\fscx100\fscy100)}" + _colour_words(text, YELLOW))


def _word_time(words, key, fallback: float) -> float:
    if key is None:
        return fallback
    k = str(key).lower().strip("*")
    for w in words:
        if re.sub(r"[^a-z0-9']", "", w.text.lower()).startswith(re.sub(r"[^a-z0-9']", "", k)):
            return w.start
    return fallback


ARROW = "m 0 0 l -70 -80 -26 -80 -26 -230 26 -230 26 -80 70 -80"  # points down, tip at 0,0
CROSS = ("m -150 -125 l -125 -150 0 -25 125 -150 150 -125 25 0 150 125 125 150 0 25 -125 150 -150 125 -25 0")
TICK = "m -140 10 l -100 -30 -40 30 110 -120 150 -80 -40 110"


def _ring(r: int) -> str:
    k = int(r * 0.552)
    return (f"m {r} 0 b {r} {k} {k} {r} 0 {r} b {-k} {r} {-r} {k} {-r} 0 "
            f"b {-r} {-k} {-k} {-r} 0 {-r} b {k} {-r} {r} {-k} {r} 0")


def scene_overlays(scene: dict, words, start: float, end: float) -> list[str]:
    """ASS events for one scene. `words` are that scene's timed words (relative times)."""
    out = []
    for ov in scene.get("overlays", []):
        t0 = start + (float(ov["at"]) if "at" in ov else _word_time(words, ov.get("on"), 0.3))
        t1 = min(end, t0 + float(ov.get("dur", end - t0)))
        if t1 <= t0:
            continue
        x, y = int(float(ov.get("x", 0.5)) * W), int(float(ov.get("y", 0.5)) * H)
        kind = ov["type"]
        pop = r"\fscx40\fscy40\t(0,140,\fscx110\fscy110)\t(140,240,\fscx100\fscy100)"
        if kind == "label":
            out.append(f"Dialogue: 3,{_ts(t0)},{_ts(t1)},Tag,,0,0,0,,"
                       + "{\\an5\\pos(" + f"{x},{y}" + ")" + pop + "}" + ov["text"].upper())
        elif kind == "arrow":
            rot = {"down": 0, "right": 90, "up": 180, "left": -90}[ov.get("dir", "down")]
            # bounce towards the target: short segments moving 30 px along the arrow
            dx, dy = {0: (0, -30), 90: (-30, 0), 180: (0, 30), -90: (30, 0)}[rot]
            t, flip = t0, False
            while t < t1:
                seg = min(0.35, t1 - t)
                a, b = ((x + dx, y + dy), (x, y)) if not flip else ((x, y), (x + dx, y + dy))
                out.append(f"Dialogue: 3,{_ts(t)},{_ts(t + seg)},Shape,,0,0,0,,"
                           + "{\\an2\\org(" + f"{x},{y}" + ")\\frz" + str(rot)
                           + "\\move(" + f"{a[0]},{a[1]},{b[0]},{b[1]}" + ")\\1c" + YELLOW
                           + "\\3c" + BLACK + "\\bord6\\p1}" + ARROW + "{\\p0}")
                t += seg
                flip = not flip
        elif kind == "ring":
            r = int(float(ov.get("r", 0.12)) * W)
            out.append(f"Dialogue: 3,{_ts(t0)},{_ts(t1)},Shape,,0,0,0,,"
                       + "{\\an5\\pos(" + f"{x},{y}" + ")\\1a&HFF&\\3c" + YELLOW + "\\bord12"
                       + r"\fscx130\fscy130\t(0,200,\fscx100\fscy100)\p1}" + _ring(r) + "{\\p0}")
        elif kind in ("cross", "tick"):
            colour, shape = (RED, CROSS) if kind == "cross" else (GREEN, TICK)
            out.append(f"Dialogue: 4,{_ts(t0)},{_ts(t1)},Shape,,0,0,0,,"
                       + "{\\an5\\pos(" + f"{x},{y}" + ")\\1c" + colour + "\\3c" + WHITE + "\\bord8"
                       + pop + "\\p1}" + shape + "{\\p0}")
        elif kind == "counter":
            a, b = int(ov.get("from", 0)), int(ov["to"])
            dur = float(ov.get("count_for", 1.2))
            steps = max(1, min(30, abs(b - a)))
            for i in range(steps + 1):
                ts = t0 + dur * i / steps
                te = t0 + dur * (i + 1) / steps if i < steps else t1
                val = round(a + (b - a) * i / steps)
                out.append(f"Dialogue: 3,{_ts(ts)},{_ts(max(te, ts + 0.04))},Tag,,0,0,0,,"
                           + "{\\an5\\pos(" + f"{x},{y}" + ")\\fscx140\\fscy140}" + f"{ov.get('prefix', '')}{val}{ov.get('suffix', '')}".upper())
        else:
            raise ValueError(f"Unknown overlay type '{kind}'. Use label, arrow, ring, cross, tick or counter")
    return out
