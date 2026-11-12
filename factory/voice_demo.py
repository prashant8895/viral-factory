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


def _diagnose(voice: str) -> bool:
    """Explain an unknown cloned voice id without printing it (public logs). True = usable."""
    import requests
    head = {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}
    pre = voice.split("_", 1)[0] if "_" in voice[:12] else "(no underscore)"
    print(f"voice id: {len(voice)} chars, kind prefix: {pre!r}, "
          f"has spaces/quotes: {any(c in voice for c in ' \'\"')}")
    ids, token, kinds = [], None, {}
    for _ in range(20):
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/voices", timeout=30, headers=head,
                         params={"page_size": 100, **({"page_token": token} if token else {})})
        if not r.ok:
            print("could not list voices:", r.status_code, r.text[:200])
            break
        js = r.json()
        for v in js.get("voices") or js.get("data") or []:
            vid = v.get("id") or v.get("name", "").split("/")[-1]
            ids.append(vid)
            kinds[v.get("type")] = kinds.get(v.get("type"), 0) + 1
            if v.get("type") != "prebuilt":
                print("  own voice:", v.get("type"), v.get("display_name"), "| same as secret:", vid == voice,
                      "| state:", v.get("state") or v.get("status"))
        token = js.get("next_page_token") or js.get("nextPageToken")
        if not token:
            break
    print(f"voices on this Gemini key's project: {kinds}; the secret's id is among them: {voice in ids}")
    t = requests.post("https://generativelanguage.googleapis.com/v1beta/interactions", timeout=120,
                      headers={**head, "Content-Type": "application/json"}, json={
                          "model": os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
                          "input": [{"type": "user_input", "content": [{"type": "text", "text": "Hello there."}]}],
                          "response_format": {"type": "audio"},
                          "generation_config": {"speech_config": [{"voice": voice}]}})
    print("one-line test with the secret's voice:", t.status_code, "" if t.ok else t.text[:200])
    return t.ok


def main(out_dir: Path = ROOT / "voice", label: str | None = None) -> Path:
    ch = json.loads((ROOT / "channels" / "curious-en" / "channel.json").read_text())
    voice = (os.environ.get("VOICE") or ch["voices"]["narrator"]).strip().removeprefix("voices/")
    if os.environ.get("LABEL") == "clone" and not _diagnose(voice):
        raise SystemExit("The cloned voice id is not usable with this Gemini key (see above)")
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
