"""Voiceover.

- Kokoro: free, open-source, runs on a normal CPU. (Curious used it until 2026-11-12.)
- Gemini: Google's acting voice (GEMINI_API_KEY). Used by Curious (English) and Drama.
  The voice can be a prebuilt name ("Iapetus") or a cloned voice id ("voice_...").
  Each line carries an acting note ("gasping, outraged"). The free tier allows 3
  requests a minute, so lines are spaced out and retried; a line that keeps failing
  stops the video (no half-done posts).

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
    emph: bool = False  # *word* or ALL-CAPS in the script: shown bigger and in orange


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


def _is_emph(raw: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", raw)
    return "*" in raw or (len(letters) >= 3 and letters.isupper())


def _spoken(text: str) -> str:
    """What the voice reads: emphasis stars removed."""
    return text.replace("*", "")


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


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
_last_gemini_call = 0.0


def _speech_span(audio, sr: int) -> tuple[float, float]:
    """Where speech starts and ends, ignoring quiet lead-in and tail."""
    win = max(1, int(0.02 * sr))
    n = len(audio) // win
    if n == 0:
        return 0.0, len(audio) / sr
    energy = np.abs(audio[: n * win]).reshape(n, win).mean(axis=1)
    loud = np.where(energy > max(energy.max() * 0.06, 1e-4))[0]
    if not len(loud):
        return 0.0, len(audio) / sr
    return loud[0] * win / sr, (loud[-1] + 1) * win / sr


def _gemini_once(text: str, voice: str, style: str) -> tuple[np.ndarray, int]:
    import base64
    import io
    import os
    import time

    import requests

    global _last_gemini_call
    wait = 21 - (time.time() - _last_gemini_call)  # free tier: 3 requests a minute
    if wait > 0:
        time.sleep(wait)
    body = {"model": os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
            "input": [{"type": "user_input", "content": [{
                "type": "text", "text": text,
                "annotations": [{"type": "speech_metadata", "style": style}] if style else []}]}],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]}}
    _last_gemini_call = time.time()
    r = requests.post(GEMINI_URL, json=body, timeout=180,
                      headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"],
                               "Content-Type": "application/json"})
    if r.status_code >= 400:
        hint = " (daily free limit may be used up: add billing to the Gemini key)" if r.status_code == 429 else ""
        raise RuntimeError(f"Gemini voice HTTP {r.status_code}{hint}: {r.text[:300]}")
    data = None
    js = r.json()
    for step in js.get("steps", []):
        for c in step.get("content", []) or []:
            if isinstance(c, dict) and c.get("data"):
                data = base64.b64decode(c["data"])
    if data is None and (js.get("output_audio") or {}).get("data"):
        data = base64.b64decode(js["output_audio"]["data"])
    if not data:
        raise RuntimeError(f"Gemini gave no audio: {str(js)[:300]}")
    if data[:4] == b"RIFF":
        with wave.open(io.BytesIO(data)) as f:
            sr, frames = f.getframerate(), f.readframes(f.getnframes())
    else:
        sr, frames = 24000, data
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768
    if len(audio) < sr * 0.3:
        raise RuntimeError("Gemini audio came back too short")
    return audio, sr


def _speak_gemini(text: str, voice: str, style: str):
    import os
    import tempfile

    from . import paid
    from .visuals import BudgetStop, with_retries  # shared retry rule: 4 tries, then stop

    key = paid.fingerprint(kind="gemini-voice", text=text, voice=voice, style=style,
                           model=os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"))
    hit = paid.cached(key, ".wav")
    if hit:  # said exactly this before: reuse, don't pay again
        with wave.open(str(hit)) as f:
            sr, frames = f.getframerate(), f.readframes(f.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768
    else:
        def once():
            paid.charge(f"Gemini voice: {text[:40]}")
            return _gemini_once(text, voice, style)
        audio, sr = with_retries(once, "Gemini voice", waits=(30, 90, 240))
        tmp = Path(tempfile.mkstemp(suffix=".wav")[1])
        _write(tmp, audio, sr)
        paid.save(key, ".wav", tmp)
    if sr != 24000:
        audio = np.interp(np.linspace(0, len(audio), int(len(audio) * 24000 / sr), endpoint=False),
                          np.arange(len(audio)), audio).astype(np.float32)
        sr = 24000
    return audio, sr, _align_by_pauses(text, audio, sr)


def _pauses(audio, sr: int, min_gap: float = 0.12) -> list[tuple[float, float]]:
    """Quiet stretches inside the speech (start, end), longest gaps are phrase breaks."""
    win = max(1, int(0.01 * sr))
    n = len(audio) // win
    if n == 0:
        return []
    energy = np.abs(audio[: n * win]).reshape(n, win).mean(axis=1)
    quiet = energy < max(energy.max() * 0.04, 1e-4)
    gaps, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * win / sr >= min_gap:
                gaps.append((start * win / sr, i * win / sr))
            start = None
    return gaps


def _align_by_pauses(text: str, audio, sr: int) -> list[Word]:
    """Gemini gives no word times. Split the line into phrases at punctuation, match each
    phrase break to one of the longest pauses in the audio (in order), then share time
    inside each phrase by word length. Keeps captions in step far better than one spread."""
    s, e = _speech_span(audio, sr)
    words = _clean_words(text)
    raw = re.split(r"\s+", text.strip())
    phrases, cur = [], []
    for r in raw:
        if re.search(r"[A-Za-z0-9]", r):
            cur.append(r)
        if re.search(r"[,.?!;:—…]$", r) and cur:
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    gaps = [g for g in _pauses(audio, sr) if s < g[0] and g[1] < e]
    k = len(phrases) - 1
    if k <= 0 or len(gaps) < k or sum(len(p) for p in phrases) != len(words):
        return _spread(words, s, e)
    breaks = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:k])
    bounds = [s] + [x for g in breaks for x in g] + [e]
    out, wi = [], 0
    for j, ph in enumerate(phrases):
        a, b = bounds[2 * j], bounds[2 * j + 1]
        out += _spread(words[wi:wi + len(ph)], a, b)
        wi += len(ph)
    return out


def _write(out: Path, audio, sr: int) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


_BAD_VOICES: set[str] = set()


def scene_lines(scene: dict) -> list[dict]:
    """A scene is either one narration or a list of {speaker, text} lines (drama)."""
    if scene.get("lines"):
        return scene["lines"]
    line = {"speaker": "narrator", "text": scene["narration"]}
    if scene.get("delivery"):  # how to say this line ("leaning in, slower"), added to the voice style
        line["delivery"] = scene["delivery"]
    return [line]


def synthesize(scene: dict, out: Path, voices: dict, speed: float = 1.05, engine: str = "kokoro",
               styles: dict | None = None) -> SceneAudio:
    """Speak one scene. Each speaker gets its own voice; lines are joined with a short gap."""
    parts, words, t, sr = [], [], 0.0, 24000
    for i, line in enumerate(scene_lines(scene)):
        speaker = line.get("speaker", "narrator")
        voice = voices.get(speaker) or voices["narrator"]
        text = _spoken(line["text"])
        if engine == "gemini":
            style = line.get("style") or (styles or {}).get(speaker, "")
            if line.get("delivery"):
                style = f"{style} For this line: {line['delivery']}."
            fallback = voices.get("_fallback")
            if voice in _BAD_VOICES and fallback:
                voice = fallback
            try:
                audio, sr, timed = _speak_gemini(text, voice, style)
            except Exception as e:
                # A cloned voice id Gemini doesn't know (wrong project, expired, typo) must
                # never stop the video: say it once and use the stock narrator instead.
                if not fallback or voice == fallback or "speaker voice" not in str(e).lower():
                    raise
                print(f"[voice] cloned voice not usable, falling back to {fallback}: {str(e)[:160]}", flush=True)
                _BAD_VOICES.add(voice)
                voice = fallback
                audio, sr, timed = _speak_gemini(text, voice, style)
        else:
            audio, sr, timed = _speak(text, voice, float(line.get("speed", speed)))
        raw = _clean_words(line["text"])
        flags = [_is_emph(r) for r in raw] if len(raw) == len(timed) else [False] * len(timed)
        words += [Word(w.text, w.start + t, w.end + t, f) for w, f in zip(timed, flags)]
        gap = np.zeros(int((0.12 if i < len(scene_lines(scene)) - 1 else 0.18) * sr), dtype=audio.dtype)
        parts += [audio, gap]
        t += (len(audio) + len(gap)) / sr
    full = np.concatenate(parts)
    _write(out, full, sr)
    return SceneAudio(out, len(full) / sr, words)
