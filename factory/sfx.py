"""Sound effects, made in code (no downloads, no licence questions).

Claude picks one per scene in the script ("sfx": "boom"); every cut also gets a
soft whoosh. `build_track` lays them on a timeline under the voice.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    a = max(1, int(attack * SR))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[a:] = np.exp(-np.linspace(0, 1, n - a) * decay)
    return e


def _bandpass_sweep(noise: np.ndarray, f0: float, f1: float) -> np.ndarray:
    """Cheap moving band-pass: a one-pole low-pass minus a lower one, with sweeping cutoffs."""
    out = np.zeros_like(noise)
    lo = hi = 0.0
    freqs = np.geomspace(f0, f1, len(noise))
    for i, x in enumerate(noise):
        a_hi = 1 - np.exp(-2 * np.pi * freqs[i] * 1.6 / SR)
        a_lo = 1 - np.exp(-2 * np.pi * freqs[i] * 0.6 / SR)
        hi += a_hi * (x - hi)
        lo += a_lo * (x - lo)
        out[i] = hi - lo
    return out


def whoosh(d=0.45):
    n = int(d * SR)
    s = _bandpass_sweep(rng.standard_normal(n), 300, 4000)
    return s * np.sin(np.linspace(0, np.pi, n)) ** 2


def boom(d=1.2):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 30 + 55 * np.exp(-t * 6)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    hit = rng.standard_normal(n) * np.exp(-t * 40) * 0.4
    return np.tanh((tone + hit) * 2.2) * _env(n, 0.004, 4)


def thud(d=0.35):
    n = int(d * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 12) + 40) / SR) * _env(n, 0.002, 9)


def pop(d=0.12):
    n = int(d * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 + 700 * np.exp(-t * 60)) / SR) * _env(n, 0.001, 18)


def ding(d=1.4):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1318, 1), (2637, 0.35), (3951, 0.15)))
    return s * _env(n, 0.002, 5) * 0.6


def riser(d=1.6):
    n = int(d * SR)
    s = _bandpass_sweep(rng.standard_normal(n), 200, 6000)
    return s * np.linspace(0, 1, n) ** 2


def sparkle(d=0.9):
    n = int(d * SR)
    out = np.zeros(n)
    for k in range(9):
        start = int(k * n / 11)
        m = int(0.12 * SR)
        f = 2000 + 400 * k
        seg = np.sin(2 * np.pi * f * np.arange(m) / SR) * _env(m, 0.001, 20) * 0.5
        out[start:start + m] += seg[: max(0, min(m, n - start))]
    return out


def boing(d=0.7):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 220 + 160 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 120 * np.exp(-t * 5)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.003, 4) * 0.7


def tick(d=1.0):
    n = int(d * SR)
    out = np.zeros(n)
    for k, f in enumerate((1800, 1200, 1800, 1200)):
        start = int(k * 0.25 * SR)
        m = int(0.03 * SR)
        out[start:start + m] += np.sin(2 * np.pi * f * np.arange(m) / SR) * _env(m, 0.0005, 30)
    return out


def crash(d=1.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = rng.standard_normal(n) * np.exp(-t * 5)
    return (s + 0.6 * thud(d)) * 0.7


SOUNDS = {"whoosh": whoosh, "boom": boom, "thud": thud, "pop": pop, "ding": ding, "riser": riser,
          "sparkle": sparkle, "boing": boing, "tick": tick, "crash": crash}
LEVEL = {"whoosh": 0.22, "boom": 0.55, "thud": 0.45, "pop": 0.35, "ding": 0.3, "riser": 0.3,
         "sparkle": 0.3, "boing": 0.4, "tick": 0.35, "crash": 0.45}


def build_track(cues: list[tuple[float, str]], total: float, out: Path) -> Path:
    """cues = [(time_in_seconds, sound_name)]. Unknown names are an error, so typos get caught."""
    track = np.zeros(int((total + 2) * SR))
    for at, name in cues:
        if name not in SOUNDS:
            raise ValueError(f"Unknown sound effect '{name}'. Use one of: {', '.join(SOUNDS)}")
        s = SOUNDS[name]()
        s = s / (np.abs(s).max() + 1e-9) * LEVEL[name]
        if name == "riser":  # a riser should peak on the cue, not start there
            at = max(0.0, at - len(s) / SR)
        i = int(at * SR)
        track[i:i + len(s)] += s[: len(track) - i]
    track = np.clip(track[: int(total * SR)], -1, 1)
    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((track * 32767).astype(np.int16).tobytes())
    return out
