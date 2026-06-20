#!/usr/bin/env python3
"""Trigger a monthly run on the durable expenses cloud agent."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from agent_api import trigger_run
from agent_prompt import monthly_prompt

AGENT_ID_FILE = Path(__file__).resolve().parents[1] / ".agent-id"


def resolve_agent_id() -> str:
    agent_id = os.environ.get("EXPENSES_AGENT_ID", "").strip()
    if not agent_id and AGENT_ID_FILE.is_file():
        agent_id = AGENT_ID_FILE.read_text().strip()
    if not agent_id:
        raise SystemExit(
            "EXPENSES_AGENT_ID not set and .agent-id missing — run setup_agent.py first"
        )
    return agent_id


def main() -> None:
    agent_id = resolve_agent_id()
    print(f"Triggering monthly run on {agent_id} …")
    result = trigger_run(agent_id, monthly_prompt())
    run_id = result.get("runId", "")
    print(json.dumps(result, indent=2))
    if run_id:
        print(f"\nDashboard: https://cursor.com/agents?id={agent_id}&runId={run_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
