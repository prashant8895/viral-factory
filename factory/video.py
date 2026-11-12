"""Turns images + voice into a finished 9:16 video with word-by-word captions."""
from __future__ import annotations

import random
import subprocess
import wave
from pathlib import Path

import numpy as np

from .tts import SceneAudio

W, H, FPS = 1080, 1920, 30
SHOT = 2.6  # seconds before the next cut (playbook: new image every 2–3 s)
ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


# ---------- motion ----------

S = 1.5  # work at 1.5x resolution so the camera move stays smooth


def _motion_filter(z0: float, z1: float, x0: float, x1: float, dur: float, focus_y: float) -> str:
    """Steady, linear camera move (no easing, so nothing bounces): zoom from z0 to z1 and
    drift the frame from x0 to x1 (0 = left edge, 0.5 = centre, 1 = right edge)."""
    p = f"min(t/{dur:.3f},1)"
    z = f"({z0}+({z1 - z0})*{p})"
    cw, ch = int(W * S), int(H * S)
    scale = f"scale=w='trunc({cw}*{z}/2)*2':h='trunc({ch}*{z}/2)*2':eval=frame:flags=bicubic"
    x = f"(iw-ow)*({x0}+({x1 - x0})*{p})"
    y = f"(ih-oh)*{focus_y:.2f}"
    return f"{scale},crop={cw}:{ch}:'{x}':'{y}'"


def still_shot(image: Path, dur: float, z0: float, z1: float, out: Path, x0: float = 0.5,
               x1: float = 0.5, focus_y: float = 0.45) -> Path:
    vf = (f"fps={FPS},{_motion_filter(z0, z1, x0, x1, dur, focus_y)},"
          f"scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-t", f"{dur:.3f}", "-i", str(image), "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", str(out)])
    return out


def probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def clip_shot(clip: Path, dur: float, out: Path, stretch: float = 1.0) -> Path:
    """Use an animated clip as-is (trimmed), or gently slowed to cover a slightly longer line."""
    vf = (f"setpts={stretch:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"setsar=1,fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-i", str(clip), "-t", f"{dur:.3f}", "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", str(out)])
    return out


def last_frame(clip: Path, out: Path) -> Path:
    run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", str(clip), "-frames:v", "1", "-q:v", "2", str(out)])
    return out


# Camera moves a scene can ask for ("motion" in the script). Each is calm and purposeful:
#   push  - slow push towards the subject, with cut-ins to tighter framings (default)
#   pull  - slow pull back, for a reveal
#   drift_left / drift_right - slow sideways glide at a fixed framing
MOTIONS = {"push", "pull", "drift_left", "drift_right"}
LEGACY = {"zoom_in": "push", "zoom_out": "pull", "pan_left": "drift_left", "pan_right": "drift_right"}


def _stills(image: Path, dur: float, motion: str, workdir: Path, tag: str) -> list[Path]:
    """Cut every 2–3 s, but every cut follows the same move, so the camera feels directed."""
    motion = LEGACY.get(motion, motion)
    if motion not in MOTIONS:
        raise ValueError(f"Unknown motion '{motion}'. Use one of: {', '.join(sorted(MOTIONS))}")
    n = max(1, round(dur / SHOT))
    d = dur / n
    shots = []
    for i in range(n):
        f = workdir / f"{tag}_{i}.mp4"
        if motion == "push":  # wide -> medium -> close, each cut slowly pushing in
            z = 1.0 + 0.12 * i
            shots.append(still_shot(image, d, z, z + 0.05, f))
        elif motion == "pull":
            z = 1.0 + 0.12 * (n - 1 - i)
            shots.append(still_shot(image, d, z + 0.05, z, f))
        else:
            span = 0.5 / n
            x0 = span * i if motion == "drift_right" else 1 - span * i
            x1 = x0 + span if motion == "drift_right" else x0 - span
            shots.append(still_shot(image, d, 1.12, 1.12, f, x0=x0, x1=x1))
    return shots


def scene_shots(image: Path, dur: float, first_move: str, seed: int, workdir: Path, tag: str,
                clip: Path | None = None) -> list[Path]:
    if clip is None:
        return _stills(image, dur, first_move, workdir, tag)
    length = probe_duration(clip)
    if dur <= length:
        return [clip_shot(clip, dur, workdir / f"{tag}_clip.mp4")]
    if dur <= length * 1.3:
        return [clip_shot(clip, dur, workdir / f"{tag}_clip.mp4", stretch=dur / length)]
    # Line runs long: play the clip, then hold on its last frame with a slow push-in.
    shots = [clip_shot(clip, length, workdir / f"{tag}_clip.mp4")]
    end = last_frame(clip, workdir / f"{tag}_last.jpg")
    return shots + _stills(end, dur - length, "push", workdir, tag + "h")


# ---------- captions ----------

def _ts(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _esc(s: str) -> str:
    return s.replace("{", "(").replace("}", ")").replace("\\", "")


def captions_ass(scenes: list[SceneAudio], hook_text: str, out: Path, job_scenes: list[dict] | None = None,
                 poster: bool = False, handle: str | None = None) -> Path:
    """Big captions, 1–3 words at a time, current word in yellow.

    poster=True: the new look. A poster-style opening title, a headline at the top of each
    scene, code-made overlays (arrows, labels...), and word captions moved to the lower third."""
    from . import overlays
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Anton,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,9,4,5,60,60,0,1
Style: Hook,Anton,108,&H0000E6FF,&H0000E6FF,&H00000000,&HB4000000,0,0,0,0,100,100,1,0,3,22,0,8,70,70,230,1
{overlays.STYLES if poster else ""}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if poster:  # word captions sit in the lower third, out of the way of headlines and overlays
        header = header.replace(",1,9,4,5,60,60,0,1", ",1,9,4,2,60,60,330,1").replace("Style: Cap,Anton,128", "Style: Cap,Anton,104")
    lines = []
    if poster:
        lines += overlays.poster(hook_text)
        t = 0.0
        for k, (sc, sa) in enumerate(zip(job_scenes or [], scenes)):
            if sc.get("headline") and k > 0:  # scene 1 is covered by the poster title
                lines.append(overlays.headline(sc["headline"], t, t + sa.duration))
            lines += overlays.scene_overlays(sc, sa.words, t, t + sa.duration)
            t += sa.duration
    else:
        # Hook text: the first 2.8 s, top of the screen, pops in.
        lines.append(f"Dialogue: 1,{_ts(0)},{_ts(2.8)},Hook,,0,0,0,,"
                     r"{\fad(0,150)\fscx70\fscy70\t(0,120,\fscx100\fscy100)}" + _esc(hook_text.upper().replace("*", "")))

    if handle:  # the page's handle, burned in so a re-upload still credits the page
        lines += overlays.handle_mark(handle, sum(sc.duration for sc in scenes))
    offset = 0.0
    for sc in scenes:
        words = sc.words
        i = 0
        while i < len(words):
            # 1–3 words per chunk; break early on punctuation so phrases read well.
            chunk = [words[i]]
            while len(chunk) < 3 and i + len(chunk) < len(words) and not chunk[-1].text[-1] in ".,?!:;" \
                    and sum(len(w.text) for w in chunk) < 14:
                chunk.append(words[i + len(chunk)])
            for k, w in enumerate(chunk):
                start = offset + w.start
                end = offset + (chunk[k + 1].start if k + 1 < len(chunk) else
                                (words[i + len(chunk)].start if i + len(chunk) < len(words) else w.end + 0.25))
                parts = []
                for j, cw in enumerate(chunk):
                    txt = _esc(cw.text.upper().strip('"“”*'))
                    if cw.emph:  # key word: orange and bigger, pops harder when spoken
                        size = "128" if j == k else "115"
                        parts.append(r"{\c&H0000A5FF&\fscx" + size + r"\fscy" + size + "}" + txt
                                     + r"{\c&H00FFFFFF&\fscx100\fscy100}")
                    elif j == k:
                        parts.append(r"{\c&H0000E6FF&}" + txt + r"{\c&H00FFFFFF&}")
                    else:
                        parts.append(txt)
                pop = r"{\fscx88\fscy88\t(0,90,\fscx100\fscy100)}" if k == 0 else ""
                lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,{pop}" + " ".join(parts))
            i += len(chunk)
        offset += sc.duration
    out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return out


# ---------- final assembly ----------

def _punch_filter(punches: list[float]) -> str:
    """A quick 8% zoom-in that eases back over 0.3 s at each punch time (hook, booms)."""
    if not punches:
        return ""
    z = "+".join(f"0.08*between(t,{a:.2f},{a + 0.3:.2f})*(1-(t-{a:.2f})/0.3)" for a in punches)
    return (f"scale=w='trunc(iw*(1+{z})/2)*2':h='trunc(ih*(1+{z})/2)*2':eval=frame,"
            f"crop={W}:{H},")


def assemble(shots: list[Path], scenes: list[SceneAudio], ass: Path, music: Path | None, out: Path,
             sfx_track: Path | None = None, punches: list[float] | None = None) -> Path:
    work = ass.parent
    lst = work / "shots.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in shots))
    silent = work / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    voice = join_voice(scenes, work / "voice.wav")

    total = sum(s.duration for s in scenes)
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(voice)]
    # The voice goes straight in; it is only split when music needs it to duck under the voice.
    # Voice polish, like a podcast mic chain: cut rumble, lift the consonant band a little so
    # words are crisp on phone speakers, tame harsh "s" sounds, even out loud and soft words.
    polish = ("highpass=f=75,equalizer=f=200:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,"
              "deesser=i=0.35,acompressor=threshold=0.125:ratio=2.5:attack=8:release=120:makeup=1.6")
    chain = [f"[1:a]aresample=48000,{polish},{'asplit=2[v][vs]' if music else 'anull[v]'}"]
    mix, n = ["[v]"], 2
    if sfx_track:
        cmd += ["-i", str(sfx_track)]
        chain.append(f"[{n}:a]aresample=48000,volume=0.9[fx]")
        mix.append("[fx]")
        n += 1
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        chain.append(f"[{n}:a]aresample=48000,volume=0.12,afade=t=in:d=0.5,"
                     f"afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5[m]")
        chain.append("[m][vs]sidechaincompress=threshold=0.05:ratio=6[md]")  # music dips under the voice
        mix.append("[md]")
        n += 1
    chain.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,"
                 "loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    af = ";".join(chain)
    sub = str(ass).replace(":", r"\:")
    cmd += ["-filter_complex", f"[0:v]{_punch_filter(punches or [])}ass='{sub}':fontsdir='{FONT_DIR}'[vout];{af}",
            "-map", "[vout]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(out)]
    run(cmd)
    check_audio(out, scenes)
    return out


def join_voice(scenes: list[SceneAudio], out: Path) -> Path:
    """All scene voices end to end, sample for sample (no ffmpeg concat, no timestamps to lose)."""
    rate, parts = None, []
    for s in scenes:
        with wave.open(str(s.path), "rb") as f:
            if f.getnchannels() != 1 or f.getsampwidth() != 2:
                raise RuntimeError(f"{s.path.name}: voice must be mono 16-bit")
            if rate is None:
                rate = f.getframerate()
            elif f.getframerate() != rate:
                raise RuntimeError(f"{s.path.name}: voice is {f.getframerate()} Hz, others are {rate} Hz")
            parts.append(f.readframes(f.getnframes()))
    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(parts))
    return out


def check_audio(video: Path, scenes: list[SceneAudio]) -> None:
    """Refuse a video whose sound has holes. Listens to the finished file itself:
    1. the decoded sound must last as long as the video (holes in the AAC stream shorten it),
    2. no gap between audio packets,
    3. while each word is spoken, the sound must actually be there."""
    total = sum(s.duration for s in scenes)
    sr = 16000
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], check=True, capture_output=True).stdout
    a = np.frombuffer(pcm, dtype=np.float32)
    heard = len(a) / sr
    if heard < total - 0.3:
        raise RuntimeError(f"Audio check: only {heard:.1f} s of sound in a {total:.1f} s video (voice missing)")
    pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "packet=pts_time",
                          "-of", "csv=p=0", str(video)], check=True, capture_output=True, text=True).stdout
    times = [float(t.strip(", ")) for t in pts.split() if t.strip(", ")]
    holes = [(x, y - x) for x, y in zip(times, times[1:]) if y - x > 0.1]
    if holes:
        ends = np.cumsum([sc.duration for sc in scenes])
        scene_at = lambda t: int(np.searchsorted(ends, t, side="right")) + 1
        where = ", ".join(f"{x:.1f}s ({d:.1f}s, scene {min(scene_at(x), len(scenes))} of {len(scenes)}, video {total:.1f}s)"
                          for x, d in holes[:5])
        raise RuntimeError(f"Audio check: {len(holes)} hole(s) in the sound at {where}")
    win = int(0.05 * sr)
    silent, spoken, t0 = [], 0, 0.0
    for k, s in enumerate(scenes):
        for w in s.words:
            i, j = int((t0 + w.start - 0.05) * sr), int((t0 + w.end + 0.05) * sr)
            seg = a[max(0, i):j]
            n = len(seg) // win
            if n < 1:
                continue
            spoken += 1
            # the loudest 50 ms inside the word: a real word always has a loud part
            rms = float(np.sqrt((seg[: n * win].reshape(n, win) ** 2).mean(axis=1)).max())
            if rms < 10 ** (-40 / 20):  # quieter than -40 dB while a word should be heard
                silent.append(f"scene {k + 1} '{w.text}' at {t0 + w.start:.1f}s")
        t0 += s.duration
    if spoken and len(silent) > max(2, spoken // 20):
        raise RuntimeError(f"Audio check: {len(silent)} of {spoken} words are silent: " + "; ".join(silent[:6]))
    print(f"[audio check] ok: {heard:.1f} s of sound, no holes, {spoken - len(silent)}/{spoken} words heard",
          flush=True)


def thumbnail(video: Path, out: Path, at: float = 0.6) -> Path:
    run(["ffmpeg", "-y", "-ss", f"{at}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(out)])
    return out
