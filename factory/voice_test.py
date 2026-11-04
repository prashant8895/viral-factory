"""One-off listening test: the same lines in Kokoro and Gemini.

    python -m factory.voice_test kokoro gemini     # writes voice-test/*.wav

Each engine gets one file per page: curious.wav (narrator) and drama.wav (scene).
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import wave
from pathlib import Path

import numpy as np
import requests

OUT = Path("voice-test")
SR = 24000

# (speaker, line, acting note). The note steers Gemini and Chatterbox; Kokoro can't act.
CURIOUS = [
    ("narrator", "This is what happens to your body if you stay awake for eleven days.",
     "calm, deep, intriguing documentary narrator, slight suspense"),
    ("narrator", "By day three, your brain starts taking tiny naps without asking you.",
     "calm, deep, a little ominous"),
]
DRAMA = [
    ("Mochi", "My cake. My birthday cake. GONE.", "gasping, outraged, theatrical diva cat"),
    ("narrator", "This morning, Granny baked Mochi a birthday cake. With a fish on top.",
     "warm, cosy storyteller"),
    ("Bruno", "I only licked the plate! I swear!", "panicked, guilty big dog, talking fast"),
    ("Granny", "Bruno. Outside. Now.", "dry, unimpressed, slow and firm"),
    ("narrator", "But nobody noticed the fish on top was missing too.",
     "low, mysterious, slowing down at the end"),
]

KOKORO_VOICES = {"narrator": "bm_george", "Mochi": "af_sky", "Bruno": "am_adam", "Granny": "bf_emma",
                 "curious": "am_michael"}
GEMINI_VOICES = {"narrator": "Charon", "Mochi": "Leda", "Bruno": "Puck", "Granny": "Gacrux",
                 "curious": "Charon"}


def _save(path: Path, audio: np.ndarray) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def _read_wav_bytes(data: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(data)) as f:
        sr, frames = f.getframerate(), f.readframes(f.getnframes())
    a = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:  # simple resample
        a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a)
    return a


def _join(parts: list[np.ndarray]) -> np.ndarray:
    gap = np.zeros(int(0.35 * SR), dtype=np.float32)
    out = []
    for p in parts:
        out += [p.astype(np.float32), gap]
    return np.concatenate(out)


def kokoro(lines, page: str) -> np.ndarray:
    from kokoro_onnx import Kokoro

    k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
    parts = []
    for spk, text, _ in lines:
        voice = KOKORO_VOICES["curious" if page == "curious" else spk]
        audio, sr = k.create(text, voice=voice, speed=1.0, lang="en-us")
        parts.append(audio)
        ref = OUT / f"ref_{'curious' if page == 'curious' else spk}.wav"
        if not ref.exists():  # Chatterbox copies these as each character's base voice
            _save(ref, audio)
    return _join(parts)


def _gemini_audio(resp: dict) -> bytes:
    for step in resp.get("steps", []):
        for c in step.get("content", []) or []:
            if isinstance(c, dict) and c.get("data") and "audio" in (c.get("type", "") + c.get("mime_type", "")):
                return base64.b64decode(c["data"])
    out = resp.get("output_audio") or {}
    if out.get("data"):
        return base64.b64decode(out["data"])
    raise RuntimeError(f"No audio in Gemini answer: {json.dumps(resp)[:400]}")


def gemini(lines, page: str) -> np.ndarray:
    key = os.environ["GEMINI_API_KEY"]
    model = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
    parts = []
    for spk, text, style in lines:
        voice = GEMINI_VOICES["curious" if page == "curious" else spk]
        body = {"model": model,
                "input": [{"type": "user_input", "content": [{
                    "type": "text", "text": text,
                    "annotations": [{"type": "speech_metadata", "style": style}]}]}],
                "response_format": {"type": "audio"},
                "generation_config": {"speech_config": [{"voice": voice}]}}
        import time
        for attempt in range(6):  # free tier: 3 requests a minute, so pace and retry
            r = requests.post("https://generativelanguage.googleapis.com/v1beta/interactions",
                              headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                              json=body, timeout=120)
            if r.status_code != 429:
                break
            time.sleep(25)
        time.sleep(21)
        if r.status_code >= 400:
            raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:400]}")
        data = _gemini_audio(r.json())
        parts.append(_read_wav_bytes(data) if data[:4] == b"RIFF"
                     else np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768)
    return _join(parts)


ENGINES = {"kokoro": kokoro, "gemini": gemini}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    failed = []
    for name in sys.argv[1:]:
        for page, lines in (("curious", CURIOUS), ("drama", DRAMA)):
            try:
                _save(OUT / f"{name}-{page}.wav", ENGINES[name](lines, page))
                print(f"made {name}-{page}.wav")
            except Exception as e:
                failed.append(f"{name}-{page}: {e}")
                print(f"FAILED {name}-{page}: {e}")
    (OUT / f"errors-{'-'.join(sys.argv[1:])}.txt").write_text("\n".join(failed) or "none")
