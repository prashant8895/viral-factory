"""Pictures step: make several free candidates per scene, so Claude can look and pick.

    python -m factory.pictures jobs/curious/x.json            # all scenes
    python -m factory.pictures jobs/curious/x.json 2 4        # only scenes 2 and 4

Writes out/pics/<id>/s<scene>_<model>_<n>.jpg and one contact sheet per scene
(sheet_s<scene>.jpg). Claude reviews the sheets, copies the best picture into
jobs/<page>/pics/<id>/s<scene>.jpg and sets "image" on that scene. Then it places
arrows and rings on what is actually in the picture.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import visuals

ROOT = Path(__file__).resolve().parent.parent
MODELS = os.environ.get("PICTURE_MODELS", "zimage,klein,microsoft/mai-image-2.6-flash").split(",")
PER_MODEL = int(os.environ.get("PICTURES_PER_MODEL", "2"))


def sheet(files: list[Path], out: Path) -> None:
    """Thumbnails side by side, each labelled with its file name, for a quick look."""
    thumbs = [Image.open(f).convert("RGB").resize((270, 480)) for f in files]
    img = Image.new("RGB", (270 * len(thumbs), 520), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(ROOT / "assets/fonts/Anton-Regular.ttf"), 18)
    for i, (t, f) in enumerate(zip(thumbs, files)):
        img.paste(t, (270 * i, 40))
        d.text((270 * i + 6, 10), f.stem, fill="black", font=font)
    img.save(out, quality=85)


def main(job_path: Path, only: list[int]) -> None:
    job = json.loads(job_path.read_text())
    style = job.get("style") or json.loads((ROOT / "channels" / job["channel"] / "channel.json").read_text())["style"]
    job["style"] = style
    out = ROOT / "out" / "pics" / job["id"]
    out.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(job["scenes"], start=1):
        if (only and i not in only) or scene.get("anim"):
            continue
        prompt = visuals.build_prompt(job, scene)
        files = []
        for model in MODELS:
            for n in range(PER_MODEL):
                f = out / f"s{i}_{model.split('/')[-1]}_{n + 1}.jpg"
                try:
                    seed = int(job.get("seed", 1)) + i * 100 + n
                    if model.startswith("gemini:"):  # paid: one picture only, never repeats
                        if n:
                            continue
                        visuals.gemini_image(prompt, seed, f, model=model.split(":", 1)[1])
                    else:
                        visuals.pollinations(prompt, seed, f, model=model)
                    files.append(f)
                    print("made", f.name, flush=True)
                except visuals.BudgetStop:
                    raise
                except Exception as e:  # one model failing is fine; the others still give options
                    print("skip", f.name, e, flush=True)
        if files:
            sheet(files, out / f"sheet_s{i}.jpg")


if __name__ == "__main__":
    main(Path(sys.argv[1]), [int(a) for a in sys.argv[2:]])
