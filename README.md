# cursor-use

Agents running on Cursor to handle personal matters. We want to scale coding assistants to become personal assistants.

Each use case is a self-contained folder (`expenses-tracker/`, …) with scripts, config, and **skills** that tell cloud agents what to do.

## Reusing this repo

1. **Fork** (or clone) and push to your GitHub account.
2. **Configure** the use case — for expenses: edit `expenses-tracker/config.toml` and add R2 secrets to `.env` locally or the [Cloud Agents environment](https://cursor.com/docs/cloud-agent/environment).
3. **Create the cloud agent** (once per fork):

```bash
export CURSOR_API_KEY="cursor_..." # pragma: allowlist secret
uv run expenses-tracker/scripts/setup_agent.py   # detects your fork from git remote
```

4. **Schedule monthly runs** — add `CURSOR_API_KEY` and `EXPENSES_AGENT_ID` as GitHub secrets; `.github/workflows/monthly-expenses.yml` triggers on the 1st. Or use **Cursor Automations** in the dashboard (built-in cron, no API).

Nothing in the automation layer is tied to a specific user — repo URL comes from your fork, bucket/categories from `config.toml`, secrets from env.

## Use cases

### expenses-tracker

Monthly pipeline: R2 PDF bills → cleaned markdown → HTML report with category breakdown and key statistics.

**Run locally:**

```bash
uv run expenses-tracker/scripts/process_bills.py
uv run expenses-tracker/scripts/clean_markdown.py draft   # agent cleans + stats
uv run expenses-tracker/scripts/clean_markdown.py push
uv run expenses-tracker/scripts/generate_report.py --force
```

**Run monthly on Cursor Cloud Agents** ([API docs](https://cursor.com/docs/cloud-agent/api/endpoints)):

```bash
export CURSOR_API_KEY="cursor_..." # pragma: allowlist secret
uv run expenses-tracker/scripts/setup_agent.py      # once
uv run expenses-tracker/scripts/trigger_monthly.py  # each month
```

See [expenses-tracker/README.md](expenses-tracker/README.md) and `expenses-tracker/skills/`.

## Adding another personal agent

Copy the pattern from `expenses-tracker/`:

| Piece | Purpose |
|-------|---------|
| `config.toml` | User-specific settings (not in skills) |
| `skills/` | Agent instructions — what to run, in what order |
| `scripts/setup_agent.py` + `trigger_*.py` | Cloud Agents API create + cron trigger |
| `.github/workflows/*.yml` | External schedule (API has no built-in cron) |

Shared API client: `expenses-tracker/lib/agent_api.py` — copy or hoist when you add a second use case.
