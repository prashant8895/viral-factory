"""Voiceover with Kokoro (free, open-source, runs on a normal CPU).

Returns the audio file plus the start and end time of every word, which the
captions need for the word-by-word pop effect.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import wave

import numpy as np

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class SceneAudio:
    path: Path
    duration: float
    words: list[Word]


_engine = None


def _kokoro():
    global _engine
    if _engine is None:
        from kokoro_onnx import Kokoro

        _engine = Kokoro(str(MODEL_DIR / "kokoro-v1.0.onnx"), str(MODEL_DIR / "voices-v1.0.bin"))
    return _engine


def _clean_words(text: str) -> list[str]:
    return [w for w in re.split(r"\s+", text.strip()) if re.search(r"[A-Za-z0-9]", w)]


def _group_timings(timings) -> list[tuple[float, float]]:
    """Group phoneme timings into words, using the spaces between them."""
    groups, cur = [], []
    for t in timings:
        if t.phoneme == " ":
            if cur:
                groups.append(cur)
            cur = []
        elif re.match(r"[^\s!\"(),.:;?—“”…]", t.phoneme):
            cur.append(t)
    if cur:
        groups.append(cur)
    return [(g[0].start, g[-1].end) for g in groups]


def _spread(words: list[str], start: float, end: float) -> list[Word]:
    """Fallback: share the time between words by their length."""
    weights = [len(w) + 2 for w in words]
    total = sum(weights)
    out, t = [], start
    for w, wt in zip(words, weights):
        d = (end - start) * wt / total
        out.append(Word(w, t, t + d))
        t += d
    return out


def _speak(text: str, voice: str, speed: float):
    """One line in one voice -> (audio array, sample rate, timed words)."""
    audio, sr, timings = _kokoro().create_timed(text, voice=voice, speed=speed, lang="en-us")
    words = _clean_words(text)
    spans = _group_timings(timings) if timings else []
    if spans and len(spans) == len(words):
        timed = [Word(w, s, e) for w, (s, e) in zip(words, spans)]
    else:
        dur = len(audio) / sr
        timed = _spread(words, spans[0][0] if spans else 0.05, spans[-1][1] if spans else dur - 0.05)
    return audio, sr, timed


def _write(out: Path, audio, sr: int) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


def scene_lines(scene: dict) -> list[dict]:
    """A scene is either one narration or a list of {speaker, text} lines (drama)."""
    if scene.get("lines"):
        return scene["lines"]
    return [{"speaker": "narrator", "text": scene["narration"]}]


def synthesize(scene: dict, out: Path, voices: dict, speed: float = 1.05) -> SceneAudio:
    """Speak one scene. Each speaker gets its own voice; lines are joined with a short gap."""
    parts, words, t, sr = [], [], 0.0, 24000
    for i, line in enumerate(scene_lines(scene)):
        voice = voices.get(line.get("speaker", "narrator")) or voices["narrator"]
        audio, sr, timed = _speak(line["text"], voice, float(line.get("speed", speed)))
        words += [Word(w.text, w.start + t, w.end + t) for w in timed]
        gap = np.zeros(int((0.12 if i < len(scene_lines(scene)) - 1 else 0.18) * sr), dtype=audio.dtype)
        parts += [audio, gap]
        t += (len(audio) + len(gap)) / sr
    full = np.concatenate(parts)
    _write(out, full, sr)
    return SceneAudio(out, len(full) / sr, words)
