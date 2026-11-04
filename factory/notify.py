"""Tell Prashant when something fails, through a GitHub issue in this repo.

GitHub sends the repo owner an email and a GitHub app notification for a new
issue that mentions them. One issue per problem: retries don't open new ones.

    python -m factory.notify fail  "Render failed: drama-2026-11-05" "details..."
    python -m factory.notify still "Render failed: drama-2026-11-05" "details..."  # final retry failed
    python -m factory.notify fixed "Render failed: drama-2026-11-05" "details..."  # closes it
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _open_issue(title: str) -> int | None:
    out = _gh("issue", "list", "--state", "open", "--search", f'in:title "{title}"',
              "--json", "number,title", "--limit", "20")
    for it in json.loads(out or "[]"):
        if it["title"] == title:
            return it["number"]
    return None


def main(kind: str, title: str, body: str) -> None:
    try:
        _main(kind, title, body)
    except Exception as e:  # an alert problem must never stop posting
        print(f"(could not send alert: {e})")


def _main(kind: str, title: str, body: str) -> None:
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    run = ""
    if os.environ.get("GITHUB_RUN_ID"):
        run = f"\n\nRun log: {os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    existing = _open_issue(title)
    if kind == "fail":
        if existing is None:  # first failure: open it (this is what notifies)
            _gh("issue", "create", "--title", title,
                "--body", f"@{owner} {body}\n\nThe factory will keep retrying. Nothing half-done is posted.{run}")
    elif kind == "still":
        msg = f"@{owner} Still failing after all retries. Nothing was posted. {body}{run}"
        if existing is None:
            _gh("issue", "create", "--title", title, "--body", msg)
        else:
            _gh("issue", "comment", str(existing), "--body", msg)
    elif kind == "fixed" and existing is not None:
        _gh("issue", "close", str(existing), "--comment", f"Fixed on retry. {body}{run}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
