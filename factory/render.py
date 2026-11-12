"""Render one job file into a finished video.

    python -m factory.render jobs/curious/2026-11-05-sleep.json

Writes out/<id>/final.mp4, thumb.jpg and meta.json, and state/<id>.json.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path

from . import anim, channels, quiz, sfx, tts, video, visuals

ROOT = Path(__file__).resolve().parent.parent


def check_job(job: dict) -> None:
    need = ["id", "channel", "hook_text", "scenes", "youtube", "instagram", "facebook"]
    missing = [k for k in need if k not in job]
    if missing:
        raise ValueError(f"Job is missing: {missing}")
    words = sum(len(tts.caption_text(l["text"]).split()) for s in job["scenes"] for l in tts.scene_lines(s))
    said = " ".join(tts.caption_text(l["text"]) for s in job["scenes"] for l in tts.scene_lines(s))
    if len(re.findall(r"oh,?\s+that'?s\s+why", said, re.I)) > 1:
        raise ValueError("Say 'oh, that's why' at most once per video")
    for s in job["scenes"]:  # delivery tags must be ones the voice knows, or they get read out
        for l in tts.scene_lines(s):
            bad = [t for t in tts.TAG_RE.findall(l["text"]) if t.lower().strip() not in tts.VOICE_TAGS]
            if bad:
                raise ValueError(f"Unknown voice tag(s) {bad} in: {l['text'][:60]!r}")
            if re.search(r"(^|[.!?]\s+)oh,?\s+that'?s\s+why\s*[!.]", tts.caption_text(l["text"]), re.I):
                raise ValueError("'Oh, that's why!' as a sentence of its own sounds abrupt (Prashant). "
                                 "Weave it into a sentence, e.g. \"that's your little 'oh, that's why' moment\".")
            if len(tts.TAG_RE.findall(l["text"])) > 2:
                raise ValueError(f"Max 2 voice tags per scene: {l['text'][:60]!r}")
    if not 40 <= words <= 160:
        raise ValueError(f"Spoken text is {words} words; playbook says 85–120 (drama 60–110)")
    check_search_text(job)
    check_engagement(job)
    if job.get("hook_style") in ("ever-wondered", "curiosity"):  # Curious house hook since 2026-11-12
        first = tts.caption_text(tts.scene_lines(job["scenes"][0])[0]["text"]).replace("*", "").strip()
        if "?" not in first:
            raise ValueError(f"Line 1 must open a real question the video answers (the 'Ever wondered why...?' idea): {first[:60]!r}")
        opener = " ".join(re.findall(r"[a-z']+", first.lower())[:3])
        for prev in _recent_openers(job):
            if prev == opener:
                raise ValueError(f'Line 1 starts like one of the last 3 videos ("{opener} ..."): vary the opening')


def _engagement(job: dict) -> dict:
    try:
        eng = channels.load(job["channel"]).get("engagement") or {}
    except Exception:
        return {}
    return eng if eng and str(job.get("date") or "") >= eng.get("since", "9999") else {}


def check_engagement(job: dict) -> None:
    """Hook + quiz rules (Prashant, 2026-11-13): grab people in the first second, re-hook in the
    middle, pay off late, end with a guess about TOMORROW's topic, and thank yesterday's fastest."""
    eng = _engagement(job)
    if not eng:
        return
    sc = job["scenes"]
    content = [s for s in sc if not s.get("quiz") and not s.get("shoutout")]
    first = tts.caption_text(tts.scene_lines(sc[0])[0]["text"]).replace("*", "")
    if len(first.split()) > eng.get("hook_max_words", 14):
        raise ValueError(f"Hook line is {len(first.split())} words; the first ~2 seconds must land it "
                         f"(max {eng.get('hook_max_words', 14)}): {first[:70]!r}")
    beats = [s.get("beat") for s in content]
    if beats[:1] != ["hook"]:
        raise ValueError('Scene 1 needs "beat": "hook"')
    if "loop" not in beats[:2]:
        raise ValueError('Scene 1 or 2 must open a loop ("beat": "loop"): a promise the video only pays off near the end')
    if "rehook" not in beats[2:-1]:
        raise ValueError('Put a "beat": "rehook" in the middle (a twist/turn, e.g. "but here\'s the weird part")')
    if "payoff" not in beats or beats.index("payoff") < len(content) // 2:
        raise ValueError('The "payoff" scene must be in the second half: keep people waiting for it')
    for s in content:
        n = sum(len(tts.caption_text(l["text"]).split()) for l in tts.scene_lines(s))
        if n > eng.get("scene_max_words", 30):
            raise ValueError(f"A scene of {n} words sits on one picture too long; split it (max {eng.get('scene_max_words', 30)})")
    q = job.get("quiz")
    if not q:
        raise ValueError('Job needs a "quiz": a guess about tomorrow\'s topic (see prompts/script.md)')
    opts = q.get("options") or {}
    if not 2 <= len(opts) <= 3 or q.get("answer") not in opts:
        raise ValueError("quiz needs 2-3 options (A, B, C) and an answer that is one of them")
    if set(q.get("keywords") or {}) != set(opts):
        raise ValueError("quiz.keywords needs a word list for every option (to judge comments)")
    for k in ("theme", "question", "next_topic"):
        if not q.get(k):
            raise ValueError(f"quiz.{k} is missing")
    if not sc[-1].get("quiz"):
        raise ValueError('The last scene must be the quiz scene ("quiz": true)')
    shout = [i for i, s in enumerate(sc) if s.get("shoutout")]
    if len(shout) > 1 or (shout and shout[0] != len(sc) - 2):
        raise ValueError("At most one shoutout scene, right before the quiz scene")
    if shout and not sc[shout[0]].get("narration_none"):
        raise ValueError('The shoutout scene needs "narration_none" (said when nobody got it right)')
    said = " ".join(tts.caption_text(l["text"]) for l in tts.scene_lines(sc[-1])).lower()
    if "comment" not in said:
        raise ValueError("The quiz scene must ask people to comment their guess")
    if "comment" not in (job.get("instagram") or {}).get("caption", "").lower():
        raise ValueError("Put the quiz question in the Instagram caption too (ask them to comment)")


def _recent_openers(job: dict, n: int = 3) -> list[str]:
    """First 3 words of line 1 of the latest n other Curious jobs, so openings don't repeat."""
    out = []
    files = sorted((ROOT / "jobs" / "curious").glob("curious-20*.json"), reverse=True)
    base = re.sub(r"-(en|hi)$", "", job.get("id", ""))
    for f in files:
        if f.stem == base or len(out) >= n:
            continue
        try:
            j = _pick(json.loads(f.read_text()), "en", {"en", "hi"})
            line = tts.caption_text(tts.scene_lines(j["scenes"][0])[0]["text"]).replace("*", "")
        except Exception:
            continue
        out.append(" ".join(re.findall(r"[a-z']+", line.lower())[:3]))
    return out


def _has(text: str, phrase: str) -> bool:
    """True when every real word of the search phrase is in the text (any order, any case)."""
    have = set(re.findall(r"[\w']+", text.lower()))
    return all(w in have for w in re.findall(r"[\w']+", phrase.lower()) if len(w) > 2)


def check_search_text(job: dict) -> None:
    """Instagram now ranks on caption words and on-screen text, not hashtags (max 5).
    So: the main search phrase must be in the first caption line and the titles,
    every search phrase somewhere in the caption, and never more than 5 hashtags."""
    texts = {
        "instagram caption": (job.get("instagram") or {}).get("caption") or "",
        "facebook description": (job.get("facebook") or {}).get("description") or "",
        "youtube description": (job.get("youtube") or {}).get("description") or "",
    }
    for where, text in texts.items():
        tags = re.findall(r"#\w+", text.replace("#shorts", ""))
        if len(tags) > 5:
            raise ValueError(f"{where} has {len(tags)} hashtags; Instagram allows 5, playbook says 3–5")
    keys = job.get("keywords")
    if not keys:
        return  # older jobs had no keywords
    main, caption = keys[0], texts["instagram caption"]
    firsts = {
        "instagram caption line 1": caption.split("\n", 1)[0],
        "facebook description line 1": texts["facebook description"].split("\n", 1)[0],
        "youtube title": (job.get("youtube") or {}).get("title") or "",
    }
    for where, text in firsts.items():
        if not _has(text, main):
            raise ValueError(f'{where} must contain the main search phrase "{main}": {text!r}')
    for k in keys[1:]:
        if not _has(caption, k):
            raise ValueError(f'instagram caption should mention the search phrase "{k}" in a sentence')


def ensure_cast(ch: dict) -> None:
    """Drama page: make each character's reference picture once, kept in the repo."""
    cast_dir = ch["dir"] / "cast"
    cast_dir.mkdir(exist_ok=True)
    for name, c in ch["cast"].items():
        ref = cast_dir / f"{name.lower()}.png"
        if not ref.exists():
            print(f"[cast] drawing {name} for the first time", flush=True)
            visuals.make_reference(name, c["look"], ch["style"], ref, seed=c.get("seed", 11))


def _pick(obj, lang: str, langs: set):
    """Resolve {"en": ..., "hi": ...} anywhere in the job to the one language."""
    if isinstance(obj, dict):
        if obj and set(obj) <= langs:
            return _pick(obj.get(lang), lang, langs)
        return {k: _pick(v, lang, langs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_pick(v, lang, langs) for v in obj]
    return obj


def render(job_path: Path) -> list[Path]:
    """Render a job. A job with "languages": ["en", "hi"] becomes one video per language
    (page <channel>-<lang>), all sharing the same pictures, so the second costs nothing extra."""
    job = json.loads(job_path.read_text())
    job.setdefault("channel", job_path.parent.name)
    langs = job.pop("languages", None)
    produced = []
    if not langs:
        produced.append(render_one(job))
    else:
        # Only languages whose page is still live get rendered (Hindi paused 2026-11-12).
        # Old jobs may still carry {"en": ..., "hi": ...} fields; those resolve fine.
        known = set(langs) | {"en", "hi"}
        live = [l for l in langs if not channels.paused(f"{job['channel']}-{l}")]
        if not live:
            raise ValueError(f"Every language page of this job is paused: {langs}")
        shared = ROOT / "out" / job["id"] / "shared"
        for lang in live:
            one = _pick(job, lang, known)
            one["id"], one["channel"], one["language"] = f"{job['id']}-{lang}", f"{job['channel']}-{lang}", lang
            produced.append(render_one(one, shared))
    (ROOT / "out" / "produced.txt").write_text("\n".join(p.parent.name for p in produced) + "\n")
    return produced


def render_one(job: dict, img_dir: Path | None = None) -> Path:
    check_job(job)
    ch = channels.load(job["channel"])
    shout = quiz.apply(job)  # yesterday's fastest right answers (or the scene is dropped)
    if job.get("quiz") and job["scenes"][-1].get("quiz"):
        q, eng = job["quiz"], ch.get("engagement") or {}
        job["scenes"][-1].setdefault("anim", "anims/quiz.html")
        job["scenes"][-1]["anim_params"] = {"theme": q["theme"], "question": q["question"],
                                            "options": q["options"], "next": q.get("next_title", ""),
                                            "footer": eng.get("quiz_footer", "FIRST 3 RIGHT = SHOUTOUT TOMORROW"),
                                            **job["scenes"][-1].get("anim_params", {})}
    if ch.get("video_model") and not os.environ.get("VIDEO_MODEL"):
        os.environ["VIDEO_MODEL"] = ch["video_model"]  # a repo variable can still override it
    job.setdefault("style", ch["style"])
    cast = ch["cast"]
    if cast:
        ensure_cast(ch)

    out_dir = ROOT / "out" / job["id"]
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)

    voices = {**ch["voices"], **{n: c["voice"] for n, c in cast.items() if c.get("voice")}}
    styles = {**ch.get("styles", {}), **{n: c["voice_style"] for n, c in cast.items() if c.get("voice_style")}}
    engine = ch.get("tts", "kokoro")
    if job.get("voice"):
        voices["narrator"] = job["voice"]
    elif engine == "gemini":
        trial = ch.get("voice_trial") or {}
        own = (channels.secret(ch, "VOICE_ID") or "").strip().removeprefix("voices/")
        pick = trial.get("voice") if trial.get("status") in ("running", "kept") else None
        pick = pick or (own if own.startswith("voice_") else None)  # ignore a secret that isn't a voice id
        if pick:
            voices["_fallback"] = voices["narrator"]  # stock voice if the clone ever fails
            voices["narrator"] = pick
    speed = float(job.get("speed", ch.get("speed", 1.0)))
    n_anim = len(job["scenes"]) if ch.get("animate_scenes") == "all" else int(ch.get("animate_scenes", 0))

    scene_audio, shots = [], []
    for i, scene in enumerate(job["scenes"]):
        print(f"[scene {i + 1}/{len(job['scenes'])}] voice", flush=True)
        scene_audio.append(tts.synthesize(scene, work / f"voice_{i}.wav", voices, speed, engine, styles))
    if engine == "gemini":  # a scene that came out whispered/murmured gets one fresh, full-voice take
        for i in tts.quiet_scenes(scene_audio, 4.0):
            print(f"[scene {i + 1}] voice came out much quieter than the rest: re-recording at full voice", flush=True)
            redo = {**job["scenes"][i], "delivery": "full clear voice at normal speaking volume, not whispering"}
            scene_audio[i] = tts.synthesize(redo, work / f"voice_{i}.wav", voices, speed, engine, styles)
    for i, scene in enumerate(job["scenes"]):
        sa = scene_audio[i]

        if scene.get("anim"):  # 2D animation drawn in code (free)
            print(f"[scene {i + 1}] 2D animation", flush=True)
            params = {**scene.get("anim_params", {}), "language": job.get("language")}
            shots.append(anim.render(ROOT / scene["anim"], sa.duration, work / f"s{i}_anim.mp4", params))
            continue

        print(f"[scene {i + 1}] picture", flush=True)
        (img_dir or work).mkdir(parents=True, exist_ok=True)
        img = (img_dir or work) / f"img_{i}.jpg"
        if not img.exists():
            visuals.make_image(job, scene, i, img, cast, ch["dir"] / "cast")

        clip = None
        if i < n_anim:
            print(f"[scene {i + 1}] animation", flush=True)
            action = scene.get("action") or visuals.build_prompt(job, scene, cast)
            clip = visuals.video_clip(img, action, sa.duration, work / f"clip_{i}.mp4")
        shots += video.scene_shots(img, sa.duration, scene.get("motion", "push"),
                                   int(job.get("seed", 1)) + i, work, f"s{i}", clip)

    ass = video.captions_ass(scene_audio, job["hook_text"], work / "captions.ass", job["scenes"],
                             poster=ch.get("look") == "poster",
                             handle=(ch.get("handles") or {}).get("instagram"))

    # Sound effects: a soft whoosh on every scene cut, plus the effect Claude picked per scene.
    cues, punches, t = [], [], 0.0
    for i, (scene, sa) in enumerate(zip(job["scenes"], scene_audio)):
        pick = scene.get("sfx") or ("boom" if i == 0 else None)
        if i > 0 and pick != "riser":
            cues.append((max(0.0, t - 0.12), "whoosh"))
        if pick:
            cues.append((t + float(scene.get("sfx_at", 0)), pick))
        if i == 0 or scene.get("punch") or pick in ("boom", "thud", "crash"):
            punches.append(t + float(scene.get("sfx_at", 0)))
        t += sa.duration
    fx = sfx.build_track(cues, t, work / "sfx.wav") if job.get("sfx", True) else None

    # Music bed: picked by mood from assets/music/<mood>-*.mp3. If the page uses music,
    # a missing library stops the video rather than posting it without music.
    use_music = job.get("music", ch.get("music", False))
    music = None
    if use_music:
        lib = ROOT / "assets" / "music"
        mood = job.get("music_mood") or ch.get("music_mood", "")
        tracks = sorted(lib.glob(f"{mood}-*.mp3")) or sorted(lib.glob("*.mp3"))
        if not tracks:
            raise RuntimeError("This page uses music but assets/music has no tracks yet")
        music = random.Random(job["id"]).choice(tracks)

    final = out_dir / "final.mp4"
    print("[assemble]", flush=True)
    video.assemble(shots, scene_audio, ass, music, final, fx, punches)
    video.thumbnail(final, out_dir / "thumb.jpg")

    yt = job["youtube"]  # the search phrases double as YouTube tags
    yt["tags"] = list(dict.fromkeys(list(job.get("keywords") or []) + list(yt.get("tags") or [])))[:15]
    meta = {k: job[k] for k in ("id", "channel", "youtube", "instagram", "facebook", "hook_text")}
    meta["language"] = job.get("language")
    meta["duration"] = round(sum(s.duration for s in scene_audio), 2)
    meta["bucket"] = job.get("bucket")
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    # State file: tells the publisher when and where this video goes.
    state_dir = ROOT / "state"
    state_dir.mkdir(exist_ok=True)
    state_file = state_dir / f"{job['id']}.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    state.update({"id": job["id"], "channel": job["channel"], "date": job.get("date"),
                  "slot": job.get("slot", ch.get("slot", "19:00")), "publish": bool(job.get("publish", False)),
                  "bucket": job.get("bucket"), "episode": job.get("episode"), "hook_text": job["hook_text"], "hook_style": job.get("hook_style"),
                  "release": f"job-{job['id']}", "duration": meta["duration"],
                  "quiz": job.get("quiz"), "shoutouts": shout or None,
                  # for the numbers review: which look and voice this video used
                  "picture_style": "illustration" if "illustration" in job["style"].lower() else "photo",
                  "voice": ("clone" if voices["narrator"].startswith("voice_")
                            and voices["narrator"] not in tts._BAD_VOICES else engine)})
    state_file.write_text(json.dumps(state, indent=2))
    print(f"done: {final} ({meta['duration']} s)")
    return final


if __name__ == "__main__":
    render(Path(sys.argv[1]))
