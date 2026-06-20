#!/usr/bin/env python3
"""One-time setup: create a durable Cursor cloud agent for monthly expenses."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from agent_api import create_agent
from agent_prompt import default_branch, default_repo_url, monthly_prompt

AGENT_ID_FILE = Path(__file__).resolve().parents[1] / ".agent-id"


def main() -> None:
    repo = default_repo_url()
    branch = default_branch()
    stable_id = os.environ.get("EXPENSES_AGENT_ID")  # optional bc-<uuid>

    print(f"Creating cloud agent for {repo} @ {branch} …")
    result = create_agent(
        prompt=monthly_prompt(),
        repo_url=repo,
        branch=branch,
        agent_id=stable_id,
    )
    agent_id = result["agentId"]
    run_id = result.get("runId", "")

    AGENT_ID_FILE.write_text(agent_id + "\n")
    print(json.dumps(result, indent=2))
    print(f"\nSaved agent id → {AGENT_ID_FILE}")
    print(f"Dashboard: https://cursor.com/agents?id={agent_id}")
    if run_id:
        print(f"Initial run: {run_id}")
    print(
        "\nNext: add CURSOR_API_KEY and EXPENSES_AGENT_ID "
        f"({agent_id}) as GitHub secrets, then enable the monthly workflow."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
