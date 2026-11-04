"""Scene images.

Providers:
- pollinations: free tier (needs a free key from enter.pollinations.ai). Default for weeks 1–2.
- Pollinations paid models (same key, paid with Pollen): image-to-video clips
  (VIDEO_MODEL) and, for the drama cast, pictures that keep the same character
  (IMAGE_EDIT_MODEL).
- placeholder: local tests only, draws a simple card.
"""
from __future__ import annotations

import os
import shutil
import time
import urllib.parse
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NEGATIVE = "text, letters, watermark, logo, signature, blurry, deformed hands, extra fingers"


def build_prompt(job: dict, scene: dict, cast: dict | None = None) -> str:
    visual = scene["visual"].replace("{character}", job.get("character", "a person"))
    for name, c in (cast or {}).items():  # {Mochi} -> full description, so every shot matches
        visual = visual.replace("{" + name + "}", f"{name}, {c['look']}")
    return f"{visual}. {job['style']}. No text, no watermark."


def _fit(img: Image.Image) -> Image.Image:
    """Crop/scale to exactly 1080x1920, with a little extra room for motion."""
    img = img.convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def pollinations(prompt: str, seed: int, out: Path) -> Path:
    key = os.environ.get("POLLINATIONS_KEY", "")
    base = os.environ.get("POLLINATIONS_URL", "https://gen.pollinations.ai/image/")
    url = base + urllib.parse.quote(prompt)
    params = {"model": os.environ.get("POLLINATIONS_MODEL", "flux"), "width": 1080, "height": 1920,
              "seed": seed, "nologo": "true", "negative_prompt": NEGATIVE}
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    last = None
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=180)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                out.write_bytes(r.content)
                _fit(Image.open(out)).save(out, quality=95)
                return out
            last = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Image generation failed: {last}")


def placeholder(prompt: str, seed: int, out: Path) -> Path:
    import random

    rnd = random.Random(seed + len(prompt))
    top = tuple(rnd.randint(20, 90) for _ in range(3))
    bottom = tuple(rnd.randint(110, 220) for _ in range(3))
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    for _ in range(14):
        r = rnd.randint(60, 260)
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255), width=3)
    font = ImageFont.truetype(str(Path(__file__).resolve().parent.parent / "assets/fonts/Anton-Regular.ttf"), 44)
    words, lines, line = prompt.split(".")[0].split(), [], ""
    for w in words:
        if len(line) + len(w) > 30:
            lines.append(line)
            line = ""
        line += w + " "
    lines.append(line)
    for i, l in enumerate(lines[:6]):
        d.text((80, 1400 + i * 60), l.strip(), font=font, fill=(255, 255, 255))
    img.save(out, quality=92)
    return out


PROVIDERS = {"pollinations": pollinations, "placeholder": placeholder}


def make_image(job: dict, scene: dict, index: int, out: Path, cast: dict | None = None,
               cast_dir: Path | None = None) -> Path:
    provider = os.environ.get("IMAGE_PROVIDER", "pollinations")
    seed = int(job.get("seed", 1)) + index * 7
    prompt = build_prompt(job, scene, cast)
    refs = [cast_dir / f"{n.lower()}.png" for n in scene.get("cast", [])] if cast_dir else []
    refs = [r for r in refs if r.exists()]
    if refs and provider != "placeholder" and _model("IMAGE_EDIT_MODEL"):
        # No quiet fallback: an off-model cast picture would be a half-done post.
        key = paid.fingerprint(kind="cast-picture", prompt=prompt, refs=[r for r in refs],
                               model=_model("IMAGE_EDIT_MODEL"))
        hit = paid.cached(key, ".jpg")
        if hit:
            shutil.copyfile(hit, out)
            return out

        def once():
            paid.charge(f"cast picture {out.stem}")
            return same_cast_image(prompt, refs, out)
        with_retries(once, "cast picture")
        paid.save(key, ".jpg", out)
        return out
    return PROVIDERS[provider](prompt, seed, out)


class StepFailed(RuntimeError):
    """A step that still failed after every retry. The video is not made or posted."""


from .paid import BudgetCap as BudgetStop  # noqa: E402  (re-exported for tts)
from . import paid  # noqa: E402


def with_retries(fn, what: str, waits=(30, 120, 300)):
    """Try, then retry after 30 s, 2 min and 5 min. Raise if it never works."""
    last = None
    for attempt, wait in enumerate((0,) + tuple(waits)):
        if wait:
            print(f"  {what}: retry {attempt} in {wait}s ({last})", flush=True)
            time.sleep(wait)
        try:
            return fn()
        except BudgetStop:
            raise  # the spending cap is never retried
        except Exception as e:  # noqa: BLE001 - every failure gets the same retry treatment
            last = f"{type(e).__name__}: {e}"[:300]
            if "Out of Pollen" in last or "Out of xAI credit" in last or "HTTP 402" in last:
                break  # retrying can't fix an empty balance; stop and alert
    raise StepFailed(f"{what} failed after {len(waits) + 1} tries: {last}")


def make_reference(name: str, look: str, style: str, out: Path, seed: int = 11) -> Path:
    """One clean character sheet picture per cast member, made once and kept in the repo."""
    prompt = (f"character reference: {name}, {look}, full body, facing camera, plain soft background, "
              f"{style}. No text.")
    provider = os.environ.get("IMAGE_PROVIDER", "pollinations")
    return PROVIDERS[provider](prompt, seed, out)


# ---------------- Pollinations paid models (animation + same-cast pictures) ----------------
# One key (POLLINATIONS_KEY) covers free pictures and paid models. Paid models draw on
# Pollen bought at enter.pollinations.ai. Once a model is set, its step must succeed
# (with retries) or the whole video stops: nothing half-done is ever posted.

GEN = "https://gen.pollinations.ai"


def _auth() -> dict:
    return {"Authorization": f"Bearer {os.environ.get('POLLINATIONS_KEY', '')}"}


def _model(var: str) -> str | None:
    return os.environ.get(var) or None


def upload(path: Path) -> str:
    """Put a local picture on Pollinations' media store so models can read it (kept 30 days)."""
    with path.open("rb") as f:
        r = requests.post("https://media.pollinations.ai/upload", headers=_auth(),
                          files={"file": (path.name, f)}, timeout=120)
    r.raise_for_status()
    data = r.json()
    url = data.get("url") or _find_url(data, (".png", ".jpg", ".jpeg", ".webp")) or data.get("id")
    if url and not str(url).startswith("http"):
        url = f"https://media.pollinations.ai/{url}"
    if not url:
        raise RuntimeError(f"Upload gave no URL: {str(data)[:200]}")
    return url


def _find_url(obj, exts: tuple[str, ...]) -> str | None:
    if isinstance(obj, str):
        return obj if obj.startswith("http") and obj.split("?")[0].lower().endswith(exts) else None
    if isinstance(obj, dict):
        for v in obj.values():
            u = _find_url(v, exts)
            if u:
                return u
    if isinstance(obj, list):
        for v in obj:
            u = _find_url(v, exts)
            if u:
                return u
    return None


def same_cast_image(prompt: str, refs: list[Path], out: Path) -> Path:
    """A scene picture that keeps the cast's look, built from their reference pictures."""
    model = _model("IMAGE_EDIT_MODEL")
    urls = [upload(r) for r in refs]
    body = {"prompt": prompt, "model": model, "image": urls if len(urls) > 1 else urls[0],
            "size": "1080x1920", "response_format": "url"}
    r = requests.post(f"{GEN}/v1/images/edits", json=body, headers=_auth(), timeout=300)
    if r.status_code == 400 and len(urls) > 1:  # model takes one reference only
        body["image"] = urls[0]
        r = requests.post(f"{GEN}/v1/images/edits", json=body, headers=_auth(), timeout=300)
    r.raise_for_status()
    data = r.json()
    item = (data.get("data") or [{}])[0]
    if item.get("b64_json"):
        import base64
        out.write_bytes(base64.b64decode(item["b64_json"]))
    else:
        out.write_bytes(requests.get(item.get("url") or _find_url(data, (".png", ".jpg", ".jpeg", ".webp")),
                                     timeout=120).content)
    _fit(Image.open(out)).save(out, quality=95)
    return out


def _video_once(image: Path, prompt: str, out: Path, model: str) -> Path:
    start = upload(image)
    text = prompt + " Smooth natural motion, expressive acting, camera mostly steady. No text."
    url = f"{GEN}/video/{urllib.parse.quote(text)}"
    params = {"model": model, "duration": int(os.environ.get("VIDEO_SECONDS", "5")),
              "aspectRatio": "9:16", "image": start}
    headers = {**_auth(), "Prefer": "respond-async"}
    r = requests.get(url, params=params, headers=headers, timeout=120)
    if r.status_code == 400:  # model doesn't take that duration: use its default
        params.pop("duration")
        r = requests.get(url, params=params, headers=headers, timeout=120)
    if r.status_code == 402:
        raise RuntimeError("Out of Pollen: top up at enter.pollinations.ai")
    if r.status_code == 200 and r.headers.get("content-type", "").startswith("video"):
        out.write_bytes(r.content)  # made before: served from cache, not charged again
        return out
    r.raise_for_status()
    job = r.json()["id"]
    for _ in range(180):  # up to 15 minutes
        st = requests.get(f"{GEN}/v1/jobs/{job}", headers=_auth(), timeout=30).json()
        if st.get("status") == "succeeded":
            res = requests.get(f"{GEN}/v1/jobs/{job}/result", headers=_auth(), timeout=300)
            res.raise_for_status()
            out.write_bytes(res.content)
            if out.stat().st_size < 50_000:
                raise RuntimeError("clip came back empty")
            return out
        if st.get("status") in ("failed", "error", "cancelled"):
            raise RuntimeError(f"video job {st.get('status')}: {str(st)[:300]}")
        time.sleep(5)
    raise RuntimeError("video job timed out")


XAI = "https://api.x.ai/v1"


def _data_uri(path: Path) -> str:
    import base64

    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _xai_once(image: Path, prompt: str, out: Path, model: str, seconds: int) -> Path:
    """Grok Imagine on xAI, bought direct (xAI's terms: you own the output)."""
    key = os.environ["XAI_API_KEY"]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    text = prompt + " Smooth natural motion, expressive acting, camera mostly steady. No text, no speech."
    body = {"model": model, "prompt": text, "image": {"url": _data_uri(image)},
            "duration": seconds, "resolution": os.environ.get("VIDEO_RESOLUTION", "720p")}
    r = requests.post(f"{XAI}/videos/generations", json=body, headers=headers, timeout=120)
    if r.status_code == 400 and "url" in r.text.lower():
        body["image"] = {"url": upload(image)}  # needs a public URL: put it on the media store
        r = requests.post(f"{XAI}/videos/generations", json=body, headers=headers, timeout=120)
    if r.status_code == 402 or "credit" in r.text.lower() and r.status_code >= 400:
        raise RuntimeError(f"Out of xAI credit (HTTP {r.status_code}): top up at console.x.ai")
    r.raise_for_status()
    rid = r.json()["request_id"]
    for _ in range(180):  # up to 15 minutes
        st = requests.get(f"{XAI}/videos/{rid}", headers=headers, timeout=30).json()
        status = st.get("status")
        if status == "done" or (st.get("video") or {}).get("url"):
            out.write_bytes(requests.get(st["video"]["url"], timeout=300).content)
            if out.stat().st_size < 50_000:
                raise RuntimeError("clip came back empty")
            return out
        if status in ("failed", "expired", "error"):
            raise RuntimeError(f"xAI video {status}: {str(st)[:300]}")
        time.sleep(5)
    raise RuntimeError("xAI video timed out")


def video_clip(image: Path, prompt: str, seconds: float, out: Path) -> Path | None:
    """Animate one picture into a ~5 s clip, with retries.

    Returns None only when no VIDEO_MODEL is set (the free, pictures-only test runs).
    Once a model is set, a clip that keeps failing stops the whole video."""
    model = _model("VIDEO_MODEL")
    if not model:
        return None
    if out.exists() and out.stat().st_size > 50_000:  # kept from an earlier try
        return out
    provider = os.environ.get("VIDEO_PROVIDER", "xai" if os.environ.get("XAI_API_KEY") else "pollinations")
    # Pay only for the seconds the line needs (xAI bills per second, 1–15 s).
    secs = max(2, min(15, int(-(-seconds // 1)))) if provider == "xai" else int(os.environ.get("VIDEO_SECONDS", "5"))
    key = paid.fingerprint(kind="clip", image=image, prompt=prompt, model=model, provider=provider,
                           seconds=secs, res=os.environ.get("VIDEO_RESOLUTION", "720p"))
    hit = paid.cached(key, ".mp4")
    if hit:  # this exact picture was animated before: reuse it
        shutil.copyfile(hit, out)
        return out

    def once():
        paid.charge(f"animation {out.stem} ({secs}s, {provider})")
        if provider == "xai":
            return _xai_once(image, prompt, out, model, secs)
        return _video_once(image, prompt, out, model)
    with_retries(once, f"animation {out.stem}")
    paid.save(key, ".mp4", out)
    return out
