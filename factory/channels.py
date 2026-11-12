"""Per-page settings: channels/<key>/channel.json (+ cast.json for the drama page)."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(key: str) -> dict:
    d = ROOT / "channels" / key
    ch = json.loads((d / "channel.json").read_text())
    cast_file = d / "cast.json"
    ch["cast"] = json.loads(cast_file.read_text()) if cast_file.exists() else {}
    ch["dir"] = d
    return ch


def paused(key: str) -> bool:
    """A page with "paused": true in its channel.json is never rendered or posted."""
    f = ROOT / "channels" / key / "channel.json"
    return f.exists() and bool(json.loads(f.read_text()).get("paused"))


def all_keys() -> list[str]:
    return sorted(p.parent.name for p in (ROOT / "channels").glob("*/channel.json"))


SHARED = {"YT_CLIENT_ID", "YT_CLIENT_SECRET"}  # one Google app serves both channels


def secret(ch_or_prefix, name: str) -> str | None:
    """Page secrets are prefixed (DRAMA_META_PAGE_TOKEN), so a page can never post to the other."""
    prefix = ch_or_prefix if isinstance(ch_or_prefix, str) else ch_or_prefix["secret_prefix"]
    if name in SHARED:
        return os.environ.get(name)
    return stored(prefix + name) or os.environ.get(prefix + name)


def stored(full_name: str) -> str | None:
    """A token renewed from the browser (YouTube connect workflow) is kept encrypted in
    tokens/<NAME>.enc, because a workflow can't write GitHub secrets. The key is the
    YT_CLIENT_SECRET secret, so the file is useless without the repo's secrets."""
    import subprocess

    f = ROOT / "tokens" / f"{full_name}.enc"
    key = os.environ.get("YT_CLIENT_SECRET")
    if not f.exists() or not key:
        return None
    r = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-a", "-A",
                        "-pass", "env:TOKEN_KEY", "-in", str(f)], capture_output=True, text=True,
                       env={**os.environ, "TOKEN_KEY": key})
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
