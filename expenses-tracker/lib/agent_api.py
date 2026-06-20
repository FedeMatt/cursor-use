"""Minimal client for the Cursor Cloud Agents API v1 (stdlib only)."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

API_BASE = "https://api.cursor.com/v1"


class AgentApiError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def _api_key() -> str:
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not key:
        raise SystemExit("CURSOR_API_KEY is not set")
    return key


def request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    auth = base64.b64encode(f"{_api_key()}:".encode()).decode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise AgentApiError(exc.code, exc.read().decode()) from exc


def create_agent(
    *,
    prompt: str,
    repo_url: str,
    branch: str = "main",
    name: str = "Monthly expenses tracker",
    agent_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "prompt": {"text": prompt},
        "repos": [{"url": repo_url, "startingRef": branch}],
        "autoCreatePR": False,
        "env": {"type": "cloud"},
    }
    if agent_id:
        payload["agentId"] = agent_id
    return request("POST", "/agents", payload)


def trigger_run(agent_id: str, prompt: str) -> dict[str, Any]:
    return request(
        "POST",
        f"/agents/{agent_id}/runs",
        {"prompt": {"text": prompt}},
    )


def get_run(agent_id: str, run_id: str) -> dict[str, Any]:
    return request("GET", f"/agents/{agent_id}/runs/{run_id}")


if __name__ == "__main__":
    # ponytail: smoke check — no network
    auth = base64.b64encode(b"cursor_test:").decode()
    assert auth == "Y3Vyc29yX3Rlc3Q6"
    assert API_BASE.endswith("/v1")
    from agent_prompt import _normalize_github_url

    assert _normalize_github_url("git@github.com:you/repo.git") == (
        "https://github.com/you/repo"
    )
    print("agent_api ok")
