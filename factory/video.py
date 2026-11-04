"""Turns images + voice into a finished 9:16 video with word-by-word captions."""
from __future__ import annotations

import random
import subprocess
from pathlib import Path

from .tts import SceneAudio

W, H, FPS = 1080, 1920, 30
SHOT = 2.6  # seconds before the next cut (playbook: new image every 2–3 s)
ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


# ---------- motion ----------

S = 1.5  # work at 1.5x resolution so the camera move stays smooth


def _motion_filter(move: str, dur: float, focus_y: float) -> str:
    """Grow the image over time (zoom) and slide a fixed window over it (pan)."""
    p = f"min(t/{dur:.3f},1)"
    ease = f"(0.5-0.5*cos(PI*{p}))"
    z0, z1 = {"zoom_in": (1.0, 1.16), "zoom_out": (1.16, 1.0)}.get(move, (1.14, 1.14))
    z = f"({z0}+({z1}-{z0})*{ease})"
    cw, ch = int(W * S), int(H * S)
    scale = (f"scale=w='trunc({cw}*{z}/2)*2':h='trunc({ch}*{z}/2)*2':eval=frame:flags=bicubic")
    if move == "pan_right":
        x = f"(iw-ow)*{ease}"
    elif move == "pan_left":
        x = f"(iw-ow)*(1-{ease})"
    else:
        x = "(iw-ow)/2"
    y = f"(ih-oh)*{focus_y:.2f}"
    return f"{scale},crop={cw}:{ch}:'{x}':'{y}'"


def still_shot(image: Path, dur: float, move: str, focus_y: float, out: Path) -> Path:
    vf = (f"fps={FPS},{_motion_filter(move, dur, focus_y)},"
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


def _stills(image: Path, dur: float, first_move: str, rnd: random.Random, workdir: Path, tag: str) -> list[Path]:
    """Split time into 2–3 s shots with different camera moves, for a fast rhythm."""
    n = max(1, round(dur / SHOT))
    moves = [first_move] + [rnd.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"]) for _ in range(n - 1)]
    return [still_shot(image, dur / n, m, [0.5, 0.25, 0.7][i % 3], workdir / f"{tag}_{i}.mp4")
            for i, m in enumerate(moves)]


def scene_shots(image: Path, dur: float, first_move: str, seed: int, workdir: Path, tag: str,
                clip: Path | None = None) -> list[Path]:
    rnd = random.Random(seed)
    if clip is None:
        return _stills(image, dur, first_move, rnd, workdir, tag)
    length = probe_duration(clip)
    if dur <= length:
        return [clip_shot(clip, dur, workdir / f"{tag}_clip.mp4")]
    if dur <= length * 1.3:
        return [clip_shot(clip, dur, workdir / f"{tag}_clip.mp4", stretch=dur / length)]
    # Line runs long: play the clip, then hold on its last frame with a slow push-in.
    shots = [clip_shot(clip, length, workdir / f"{tag}_clip.mp4")]
    end = last_frame(clip, workdir / f"{tag}_last.jpg")
    return shots + _stills(end, dur - length, "zoom_in", rnd, workdir, tag + "h")


# ---------- captions ----------

def _ts(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _esc(s: str) -> str:
    return s.replace("{", "(").replace("}", ")").replace("\\", "")


def captions_ass(scenes: list[SceneAudio], hook_text: str, out: Path) -> Path:
    """Big centred captions, 1–3 words at a time, current word in yellow."""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Anton,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,9,4,5,60,60,0,1
Style: Hook,Anton,108,&H0000E6FF,&H0000E6FF,&H00000000,&HB4000000,0,0,0,0,100,100,1,0,3,22,0,8,70,70,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    # Hook text: the first 2.8 s, top of the screen, pops in.
    lines.append(f"Dialogue: 1,{_ts(0)},{_ts(2.8)},Hook,,0,0,0,,"
                 r"{\fad(0,150)\fscx70\fscy70\t(0,120,\fscx100\fscy100)}" + _esc(hook_text.upper()))

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
                    txt = _esc(cw.text.upper().strip('"“”'))
                    parts.append(r"{\c&H0000E6FF&}" + txt + r"{\c&H00FFFFFF&}" if j == k else txt)
                pop = r"{\fscx88\fscy88\t(0,90,\fscx100\fscy100)}" if k == 0 else ""
                lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,{pop}" + " ".join(parts))
            i += len(chunk)
        offset += sc.duration
    out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return out


# ---------- final assembly ----------

def assemble(shots: list[Path], scenes: list[SceneAudio], ass: Path, music: Path | None, out: Path) -> Path:
    work = ass.parent
    lst = work / "shots.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in shots))
    silent = work / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    alst = work / "voice.txt"
    alst.write_text("".join(f"file '{s.path.resolve()}'\n" for s in scenes))
    voice = work / "voice.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst), "-c", "copy", str(voice)])

    total = sum(s.duration for s in scenes)
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(voice)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        af = ("[1:a]aresample=48000,asplit=2[v][vs];[2:a]aresample=48000,volume=0.12,"
              f"afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5[m];"
              "[m][vs]sidechaincompress=threshold=0.05:ratio=6[md];"
              "[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        af = "[1:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    sub = str(ass).replace(":", r"\:")
    cmd += ["-filter_complex", f"[0:v]ass='{sub}':fontsdir='{FONT_DIR}'[vout];{af}",
            "-map", "[vout]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(out)]
    run(cmd)
    return out


def thumbnail(video: Path, out: Path, at: float = 0.6) -> Path:
    run(["ffmpeg", "-y", "-ss", f"{at}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(out)])
    return out
