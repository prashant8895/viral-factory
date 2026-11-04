"""Render one job file into a finished video.

    python -m factory.render jobs/curious/2026-11-05-sleep.json

Writes out/<id>/final.mp4, thumb.jpg and meta.json, and state/<id>.json.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from . import channels, sfx, tts, video, visuals

ROOT = Path(__file__).resolve().parent.parent


def check_job(job: dict) -> None:
    need = ["id", "channel", "hook_text", "scenes", "youtube", "instagram", "facebook"]
    missing = [k for k in need if k not in job]
    if missing:
        raise ValueError(f"Job is missing: {missing}")
    words = sum(len(l["text"].split()) for s in job["scenes"] for l in tts.scene_lines(s))
    if not 40 <= words <= 160:
        raise ValueError(f"Spoken text is {words} words; playbook says 85–120 (drama 60–110)")


def ensure_cast(ch: dict) -> None:
    """Drama page: make each character's reference picture once, kept in the repo."""
    cast_dir = ch["dir"] / "cast"
    cast_dir.mkdir(exist_ok=True)
    for name, c in ch["cast"].items():
        ref = cast_dir / f"{name.lower()}.png"
        if not ref.exists():
            print(f"[cast] drawing {name} for the first time", flush=True)
            visuals.make_reference(name, c["look"], ch["style"], ref, seed=c.get("seed", 11))


def render(job_path: Path) -> Path:
    job = json.loads(job_path.read_text())
    job.setdefault("channel", job_path.parent.name)
    check_job(job)
    ch = channels.load(job["channel"])
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
    speed = float(job.get("speed", ch.get("speed", 1.0)))
    n_anim = len(job["scenes"]) if ch.get("animate_scenes") == "all" else int(ch.get("animate_scenes", 0))

    scene_audio, shots = [], []
    for i, scene in enumerate(job["scenes"]):
        print(f"[scene {i + 1}/{len(job['scenes'])}] voice", flush=True)
        sa = tts.synthesize(scene, work / f"voice_{i}.wav", voices, speed, engine, styles)
        scene_audio.append(sa)

        print(f"[scene {i + 1}] picture", flush=True)
        img = work / f"img_{i}.jpg"
        if not img.exists():
            visuals.make_image(job, scene, i, img, cast, ch["dir"] / "cast")

        clip = None
        if i < n_anim:
            print(f"[scene {i + 1}] animation", flush=True)
            action = scene.get("action") or visuals.build_prompt(job, scene, cast)
            clip = visuals.video_clip(img, action, sa.duration, work / f"clip_{i}.mp4")
        shots += video.scene_shots(img, sa.duration, scene.get("motion", "zoom_in"),
                                   int(job.get("seed", 1)) + i, work, f"s{i}", clip)

    ass = video.captions_ass(scene_audio, job["hook_text"], work / "captions.ass")

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

    meta = {k: job[k] for k in ("id", "channel", "youtube", "instagram", "facebook", "hook_text")}
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
                  "bucket": job.get("bucket"), "episode": job.get("episode"), "hook_text": job["hook_text"],
                  "release": f"job-{job['id']}", "duration": meta["duration"]})
    state_file.write_text(json.dumps(state, indent=2))
    print(f"done: {final} ({meta['duration']} s)")
    return final


if __name__ == "__main__":
    render(Path(sys.argv[1]))
