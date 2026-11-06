"""2D animated scenes, drawn in code (free).

A scene with "anim": "anims/<name>.html" is rendered from that page instead of a picture.
The page draws a 1080x1920 canvas and exposes window.draw(t, duration, params):
t is seconds into the scene, params comes from the scene's "anim_params" (already in the
right language). Keep the top fifth and the lower third calm: headlines and captions sit there.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

FPS = 30
ROOT = Path(__file__).resolve().parent.parent


def render(html: Path, duration: float, out: Path, params: dict | None = None) -> Path:
    from playwright.sync_api import sync_playwright

    frames = out.parent / f"{out.stem}_frames"
    frames.mkdir(parents=True, exist_ok=True)
    n = max(1, round(duration * FPS))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.goto(html.resolve().as_uri())
        page.wait_for_function("typeof window.draw === 'function'")
        for i in range(n):
            page.evaluate("([t, d, p]) => window.draw(t, d, p)", [i / FPS, duration, params or {}])
            page.screenshot(path=str(frames / f"f{i:05d}.png"))
        browser.close()
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"),
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-an", str(out)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return out
