"""Guards for anything that costs money (Gemini voice, Pollen pictures and clips).

1. Pay once: every paid result is saved under paid-cache/ by a fingerprint of exactly
   what was asked (text, voice, picture, model...). A retry, a re-render or the same
   line tomorrow reuses the saved file instead of paying again. GitHub keeps the
   folder between runs (actions/cache).
2. Hard cap: at most MAX_PAID_CALLS paid requests per run (default 40). A bug or a
   retry loop can never run up a bill; the run stops and you get an alert instead.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "paid-cache"


class BudgetCap(RuntimeError):
    pass


def fingerprint(**parts) -> str:
    h = hashlib.sha256()
    for k in sorted(parts):
        v = parts[k]
        if isinstance(v, Path):
            v = hashlib.sha256(v.read_bytes()).hexdigest()
        h.update(f"{k}={json.dumps(v, sort_keys=True, default=str)}|".encode())
    return h.hexdigest()[:32]


def cached(key: str, ext: str) -> Path | None:
    f = CACHE / f"{key}{ext}"
    return f if f.exists() and f.stat().st_size > 0 else None


def save(key: str, ext: str, src: Path) -> None:
    CACHE.mkdir(exist_ok=True)
    shutil.copyfile(src, CACHE / f"{key}{ext}")


def _counter() -> Path:
    # One count per GitHub run, shared by every retry inside that run.
    return CACHE / f".calls-{os.environ.get('GITHUB_RUN_ID', 'local')}"


def charge(what: str) -> None:
    """Call right before every paid request."""
    cap = int(os.environ.get("MAX_PAID_CALLS", "40"))
    CACHE.mkdir(exist_ok=True)
    f = _counter()
    used = int(f.read_text()) if f.exists() else 0
    if used >= cap:
        raise BudgetCap(f"Stopped before {what}: this run already made {cap} paid requests "
                        "(MAX_PAID_CALLS). Nothing more was spent.")
    f.write_text(str(used + 1))
    print(f"  [paid {used + 1}/{cap}] {what}", flush=True)
