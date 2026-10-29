"""GitHub metadata without the octokit: plain urllib, optional token, on-disk cache."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/{owner}/{repo}"
CACHE_TTL = 60 * 30
UA = "starcheck/0.4 (+https://github.com/chxhwc/starcheck)"


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(
        os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "starcheck"
    )
    path = Path(base)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        path = Path(tempfile.gettempdir()) / "starcheck"
        path.mkdir(parents=True, exist_ok=True)
    return path


def parse_target(target: str):
    """Accept owner/repo, https://github.com/o/r, git@github.com:o/r.git."""
    m = re.search(r"github\.com[:/]+([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", target)
    if not m:
        m = re.fullmatch(r"([\w.-]+)/([\w.-]+)", target.strip())
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if owner in (".", "..") or repo in (".", ".."):
        return None
    return owner, repo


def _get(url: str, token: str = "", timeout: int = 10):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_with_retry(url: str, token: str = "", attempts: int = 3):
    """One transient 5xx / reset should not silently drop 12 weight of checks."""
    last = None
    for i in range(attempts):
        try:
            return _get(url, token)
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (403, 404):
                raise  # rate limited or missing: retrying will not help
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last = exc
        time.sleep(0.6 * (i + 1))
    raise last if last else RuntimeError("unreachable")


def fetch(owner: str, repo: str, ttl: int = CACHE_TTL) -> dict:
    cached = cache_dir() / f"{owner}__{repo}.json"
    if cached.exists() and time.time() - cached.stat().st_mtime < ttl:
        try:
            return json.loads(cached.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    try:
        raw = _get_with_retry(API.format(owner=owner, repo=repo), token)
    except Exception:
        return {}

    meta = {
        "name": raw.get("name", ""),
        "full_name": raw.get("full_name", ""),
        "description": raw.get("description") or "",
        "homepage": raw.get("homepage") or "",
        "topics": raw.get("topics") or [],
        "stars": raw.get("stargazers_count", 0),
        "forks": raw.get("forks_count", 0),
        "open_issues": raw.get("open_issues_count", 0),
        "language": raw.get("language") or "",
        "has_pages": bool(raw.get("has_pages")),
        "latest_release": "",
        "archived": bool(raw.get("archived")),
        "owner": (raw.get("owner") or {}).get("login", owner),
    }

    try:
        release = _get(API.format(owner=owner, repo=repo) + "/releases/latest", token, 8)
        meta["latest_release"] = release.get("tag_name", "")
    except Exception:
        pass

    try:
        cached.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return meta


def shallow_clone(owner: str, repo: str, dest: Path) -> bool:
    """Clone just enough to audit. Returns True on success."""
    url = f"https://github.com/{owner}/{repo}.git"
    try:
        proc = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", "--no-tags", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
