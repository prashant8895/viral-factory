"""Make a Gemini copy of YOUR voice for the narrator (run once, on your laptop).

You need two recordings of yourself, same mic, quiet room (phone voice memo is fine):
  1. sample:  10-30 seconds of you talking naturally, like you'd narrate a video.
  2. consent: you reading exactly this sentence (Google requires it):
     "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model."

Then:
    pip install requests
    GEMINI_API_KEY=... python tools/clone_voice.py sample.m4a consent.m4a

It converts both to 24 kHz mono WAV (needs ffmpeg), creates the voice, writes a 10-second
test (clone_test.wav) so you can hear it, and prints the voice id. Put that id in the GitHub
secret CURIOUS_EN_VOICE_ID and every next video uses your voice (delete the secret to go back
to the stock Gemini voice). Cost: the same as the normal Gemini voice, about Rs 1 a video.
The stored voice lasts 1 year on Google's side; run this again to renew it.
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

API = "https://generativelanguage.googleapis.com/v1beta"
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")


def wav24k(path: str) -> bytes:
    out = Path(tempfile.mkstemp(suffix=".wav")[1])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "24000",
                    "-sample_fmt", "s16", str(out)], check=True)
    return out.read_bytes()


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("Set GEMINI_API_KEY first")
    head = {"x-goog-api-key": key, "Content-Type": "application/json"}
    sample, consent = wav24k(sys.argv[1]), wav24k(sys.argv[2])
    secs = (len(sample) - 44) / 48000
    if not 10 <= secs <= 30:
        sys.exit(f"The sample is {secs:.0f} s; Google wants 10-30 s of speech. Trim it and try again.")
    r = requests.post(f"{API}/voices", headers=head, timeout=120, json={
        "store": True,
        "voice": {"model": MODEL, "type": "replicated", "display_name": "Oh That's Why narrator",
                  "replicated": {
                      "source_audio": {"mime_type": "audio/wav", "data": base64.b64encode(sample).decode()},
                      "consent_audio": {"mime_type": "audio/wav", "data": base64.b64encode(consent).decode()}}}})
    if r.status_code >= 400:
        sys.exit(f"Google refused the voice (HTTP {r.status_code}): {r.text[:400]}")
    js = r.json()
    voice_id = js.get("id") or (js.get("voice") or {}).get("id") or js.get("name", "").split("/")[-1]
    print("Voice created:", voice_id)

    t = requests.post(f"{API}/interactions", headers=head, timeout=180, json={
        "model": MODEL, "response_format": {"type": "audio"},
        "input": [{"type": "user_input", "content": [{
            "type": "text", "text": "Ever wondered why car tyres are always black? Rubber is actually white. Here's the trick.",
            "annotations": [{"type": "speech_metadata", "style": "warm, curious storyteller, clear and natural"}]}]}],
        "generation_config": {"speech_config": [{"voice": voice_id}]}})
    if t.ok:
        data = None
        for step in t.json().get("steps", []):
            for c in step.get("content", []) or []:
                if isinstance(c, dict) and c.get("data"):
                    data = base64.b64decode(c["data"])
        if data:
            Path("clone_test.raw" if data[:4] != b"RIFF" else "clone_test.wav").write_bytes(data)
            print("Listen to clone_test.wav (24 kHz). If you like it:")
    else:
        print("Test line failed:", t.status_code, t.text[:200])
    print(f"\nGitHub -> Settings -> Secrets and variables -> Actions -> New secret\n"
          f"  name:  CURIOUS_EN_VOICE_ID\n  value: {voice_id}")


if __name__ == "__main__":
    main()
