"""Speak the same short demo script in one voice, so voices can be compared side by side.

    VOICE=Iapetus python -m factory.voice_demo      # writes voice/demo_Iapetus.mp3

VOICE can be a prebuilt Gemini voice name or a cloned voice id; blank = the page's narrator.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np

from . import tts

ROOT = Path(__file__).resolve().parent.parent
LINES = [
    "Ever wondered why car tyres are always black?",
    "Here's the surprise: natural rubber is actually milky white.",
    "Tyre makers mix in a fine black powder called carbon black.",
    "It makes the rubber much tougher, so the tyre lasts thousands of kilometres longer.",
    "It also blocks the sun's UV rays, which would otherwise crack the rubber.",
    "So that's why tyres are black: it's not style, it's strength.",
    "Send this to the friend who's always on the road.",
]


def _diagnose(voice: str) -> None:
    """Explain an unknown cloned voice id without printing it (public logs)."""
    import requests
    print(f"voice id: {len(voice)} chars, starts with 'voice_': {voice.startswith('voice_')}, "
          f"has spaces/quotes: {any(c in voice for c in ' \'\"')}")
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/voices", timeout=30,
                     headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    if not r.ok:
        print("could not list voices:", r.status_code, r.text[:200])
        return
    js = r.json()
    items = js.get("voices") or js.get("data") or []
    ids = [(v.get("id") or v.get("name", "").split("/")[-1]) for v in items]
    print(f"voices on this Gemini key's project: {len(ids)}; the secret's id is among them: {voice in ids}")
    for v in items:
        print("  -", v.get("type"), v.get("display_name"), v.get("state") or v.get("status") or "")


def main(out_dir: Path = ROOT / "voice", label: str | None = None) -> Path:
    ch = json.loads((ROOT / "channels" / "curious-en" / "channel.json").read_text())
    voice = (os.environ.get("VOICE") or ch["voices"]["narrator"]).strip().removeprefix("voices/")
    if os.environ.get("LABEL") == "clone":
        _diagnose(voice)
    style = ch["styles"]["narrator"]
    parts = []
    for text in LINES:
        for attempt in range(4):
            try:
                a, sr = tts._gemini_once(text, voice, style)
                break
            except Exception as e:  # free tier: 3 a minute; wait and retry
                print("retry:", str(e)[:200])
                time.sleep(30 * (attempt + 1))
        else:
            raise SystemExit("Gemini voice kept failing")
        if sr != 24000:
            a = np.interp(np.linspace(0, len(a), int(len(a) * 24000 / sr), endpoint=False),
                          np.arange(len(a)), a).astype(np.float32)
        s, e = tts._speech_span(a, 24000)
        parts += [a[int(max(0, s - 0.05) * 24000):int((e + 0.08) * 24000)], np.zeros(int(0.28 * 24000), np.float32)]
    out_dir.mkdir(parents=True, exist_ok=True)
    wav = out_dir / "demo.wav"
    tts._write(wav, np.concatenate(parts), 24000)
    label = label or os.environ.get("LABEL") or voice
    mp3 = out_dir / f"demo_{label}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "128k", str(mp3)], check=True)
    wav.unlink()
    print("wrote", mp3, round(sum(len(p) for p in parts) / 24000, 1), "s")
    return mp3


if __name__ == "__main__":
    main()
