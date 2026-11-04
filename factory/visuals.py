"""Scene images.

Providers:
- pollinations: free tier (needs a free key from enter.pollinations.ai). Default for weeks 1–2.
- fal: paid. Image-to-video clips (FAL_VIDEO_MODEL) and, for the drama cast,
  pictures that keep the same character (FAL_IMAGE_EDIT_MODEL). Needs FAL_KEY.
- placeholder: local tests only, draws a simple card.
"""
from __future__ import annotations

import os
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
    if refs and provider != "placeholder" and _fal_ready("FAL_IMAGE_EDIT_MODEL"):
        try:
            return fal_image(prompt, refs, out)
        except Exception as e:  # fall back to text-only description
            print("  cast image failed, using description only:", e)
    return PROVIDERS[provider](prompt, seed, out)


def make_reference(name: str, look: str, style: str, out: Path, seed: int = 11) -> Path:
    """One clean character sheet picture per cast member, made once and kept in the repo."""
    prompt = (f"character reference: {name}, {look}, full body, facing camera, plain soft background, "
              f"{style}. No text.")
    provider = os.environ.get("IMAGE_PROVIDER", "pollinations")
    return PROVIDERS[provider](prompt, seed, out)


# ---------------- fal.ai (paid) ----------------

def _fal_ready(model_var: str) -> bool:
    return bool(os.environ.get("FAL_KEY") and os.environ.get(model_var))


def _data_uri(path: Path) -> str:
    import base64
    import mimetypes

    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _find_url(obj, exts: tuple[str, ...]) -> str | None:
    """fal models answer in slightly different shapes; find the first media URL."""
    if isinstance(obj, str):
        return obj if obj.startswith("http") and obj.split("?")[0].lower().endswith(exts) else None
    if isinstance(obj, dict):
        for k in ("video", "images", "image", "url", "output"):
            if k in obj:
                u = _find_url(obj[k], exts)
                if u:
                    return u
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


def _fal_run(model: str, bodies: list[dict], exts: tuple[str, ...], timeout_s: int = 600) -> str:
    """Try each input shape in turn (models differ on field names), then wait for the result."""
    headers = {"Authorization": f"Key {os.environ['FAL_KEY']}", "Content-Type": "application/json"}
    last = None
    for body in bodies:
        r = requests.post(f"https://queue.fal.run/{model}", json=body, headers=headers, timeout=120)
        if r.status_code == 422:
            last = r.text[:300]
            continue
        r.raise_for_status()
        job = r.json()
        waited = 0
        while waited < timeout_s:
            st = requests.get(job["status_url"], headers=headers, timeout=30).json()
            if st.get("status") == "COMPLETED":
                res = requests.get(job["response_url"], headers=headers, timeout=60)
                res.raise_for_status()
                url = _find_url(res.json(), exts)
                if not url:
                    raise RuntimeError(f"No media in fal answer: {str(res.json())[:300]}")
                return url
            if st.get("status") in ("FAILED", "ERROR"):
                raise RuntimeError(f"fal failed: {st}")
            time.sleep(5)
            waited += 5
        raise RuntimeError("fal timed out")
    raise RuntimeError(f"fal rejected every input shape: {last}")


def fal_image(prompt: str, refs: list[Path], out: Path) -> Path:
    uris = [_data_uri(r) for r in refs]
    bodies = [{"prompt": prompt, "image_urls": uris, "aspect_ratio": "9:16"},
              {"prompt": prompt, "image_url": uris[0], "aspect_ratio": "9:16"},
              {"prompt": prompt, "image_url": uris[0]}]
    url = _fal_run(os.environ["FAL_IMAGE_EDIT_MODEL"], bodies, (".png", ".jpg", ".jpeg", ".webp"))
    out.write_bytes(requests.get(url, timeout=120).content)
    _fit(Image.open(out)).save(out, quality=95)
    return out


def video_clip(image: Path, prompt: str, seconds: float, out: Path) -> Path | None:
    """Animate one picture into a short clip. Returns None when no video key is set,
    and the factory falls back to camera motion on the still."""
    if not _fal_ready("FAL_VIDEO_MODEL"):
        return None
    uri = _data_uri(image)
    dur = 5 if seconds <= 6 else 10
    motion = prompt + " Smooth natural motion, expressive acting, camera mostly steady."
    bodies = [{"prompt": motion, "image_url": uri, "duration": str(dur), "aspect_ratio": "9:16"},
              {"prompt": motion, "image_url": uri, "duration": dur},
              {"prompt": motion, "image_url": uri}]
    try:
        url = _fal_run(os.environ["FAL_VIDEO_MODEL"], bodies, (".mp4", ".mov", ".webm"), timeout_s=900)
    except Exception as e:
        print("  video clip failed, using still with camera motion:", e)
        return None
    out.write_bytes(requests.get(url, timeout=300).content)
    return out



