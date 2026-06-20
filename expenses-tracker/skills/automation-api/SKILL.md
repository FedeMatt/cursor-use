---
name: expenses-automation-api
description: Configure monthly expenses-tracker runs via the Cursor Cloud Agents API (POST /v1/agents). Use when setting up programmatic scheduling, GitHub Actions cron, or API-based triggers instead of the Cursor Automations UI.
---

# Cloud Agents API automation

The [Cloud Agents API](https://cursor.com/docs/cloud-agent/api/endpoints) has **no built-in cron**. Monthly scheduling needs an external trigger (GitHub Actions, Cloudflare Cron, etc.) that calls **Create A Run** on a durable agent.

## Architecture

```
One-time setup                    Every month (cron)
─────────────────                 ──────────────────
POST /v1/agents          →        POST /v1/agents/{id}/runs
(creates bc-* agent +              (same prompt, new run)
 first run)
```

Alternative: keep using **Cursor Automations** in the dashboard (built-in cron) — no API needed.

## Prerequisites

1. **Fork** this repo (or clone your own) and customize [config.toml](../../config.toml) — see [skills/config/SKILL.md](../config/SKILL.md)
2. **API key** — [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations) → create key → `CURSOR_API_KEY`
3. **Repo access** — key owner must have access to **your fork** on GitHub
4. **R2 secrets** — add in [Cloud Agents environment settings](https://cursor.com/docs/cloud-agent/environment) (recommended over `envVars`, which is beta):
   - `R2_ACCOUNT_ID` or `ACCOUNT_ID`
   - `R2_ACCESS_KEY_ID` or `ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY` or `SECRET_ACCESS_KEY`
   - `R2_BUCKET` or `BUCKET_NAME` — your bucket name

## One-time setup

```bash
export CURSOR_API_KEY="cursor_..." # pragma: allowlist secret
uv run expenses-tracker/scripts/setup_agent.py
```

This calls `POST /v1/agents` with:
- `repos`: your fork's GitHub URL @ `main` (auto-detected from `git remote origin`, or set `EXPENSES_REPO_URL`)
- `autoCreatePR`: `false`
- Prompt points at `skills/pipeline/SKILL.md` (single source of truth)

Output: `agentId` (e.g. `bc-…`) saved to `expenses-tracker/.agent-id`.

Optional stable id (idempotent recreate):

```bash
export EXPENSES_AGENT_ID="bc-$(uuidgen | tr '[:upper:]' '[:lower:]')"
uv run expenses-tracker/scripts/setup_agent.py
```

## Monthly trigger

Manual:

```bash
export CURSOR_API_KEY="cursor_..." # pragma: allowlist secret
export EXPENSES_AGENT_ID="bc-..."   # or rely on .agent-id
uv run expenses-tracker/scripts/trigger_monthly.py
```

This calls `POST /v1/agents/{agentId}/runs` with the same monthly prompt.

## GitHub Actions (recommended scheduler)

Workflow: `.github/workflows/monthly-expenses.yml` — runs `0 9 1 * *` (09:00 UTC, 1st of month).

Add repository secrets:

| Secret | Value |
|--------|-------|
| `CURSOR_API_KEY` | Your Cursor API key |
| `EXPENSES_AGENT_ID` | `bc-…` from setup |

The workflow only **triggers** the cloud agent; the agent runs on Cursor's VM with R2 secrets from the dashboard.

## API reference (this repo)

| Script | API |
|--------|-----|
| `scripts/setup_agent.py` | `POST /v1/agents` |
| `scripts/trigger_monthly.py` | `POST /v1/agents/{id}/runs` |
| `lib/agent_api.py` | stdlib HTTP client |

## vs Cursor Automations UI

| | Automations UI | Cloud Agents API |
|--|----------------|------------------|
| Schedule | Built-in cron | External (GH Actions, etc.) |
| Setup | Point-and-click | `setup_agent.py` once |
| Monthly run | Automatic | `trigger_monthly.py` or workflow |
| Best for | Quick personal setup | CI integration, custom triggers |

Both can run the same pipeline prompt; pick one scheduler, not both unless you want duplicate runs.

## Monitoring

After trigger, open the dashboard URL printed by the script, or:

```bash
curl -u "$CURSOR_API_KEY:" \
  "https://api.cursor.com/v1/agents/$EXPENSES_AGENT_ID/runs/$RUN_ID"
```

Webhooks for run completion are **coming soon** on v1 (still on [v0 webhooks](https://cursor.com/docs/cloud-agent/api/webhooks) today).
