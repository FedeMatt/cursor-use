"""Cloud-agent prompt and repo resolution for expenses-tracker."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]


def monthly_prompt() -> str:
    # ponytail: single source of truth — edit skills/pipeline/SKILL.md, not this string
    return (
        "You are the monthly expenses-tracker cloud agent.\n\n"
        "Read and execute expenses-tracker/skills/pipeline/SKILL.md in full "
        "(including clean and report skills it references).\n\n"
        "If REPORT_EMAIL_TO is set, run send_report.py after generate_report.py.\n\n"
        "R2 credentials are in the cloud environment secrets, not in git. "
        "Do NOT open a pull request."
    )


def _normalize_github_url(raw: str) -> str:
    raw = raw.strip().removesuffix(".git")
    if raw.startswith("https://github.com/"):
        return raw
    m = re.match(r"git@github\.com:(.+/.+)$", raw)
    if m:
        return f"https://github.com/{m.group(1)}"
    raise ValueError(f"unsupported git remote URL: {raw!r}")


def default_repo_url() -> str:
    if url := os.environ.get("EXPENSES_REPO_URL", "").strip():
        return _normalize_github_url(url)
    try:
        raw = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return _normalize_github_url(raw)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        raise SystemExit(
            "Cannot resolve repo URL — set EXPENSES_REPO_URL "
            "(https://github.com/you/your-fork) or run from a git clone with origin"
        )


def default_branch() -> str:
    return os.environ.get("EXPENSES_REPO_BRANCH", "main")
