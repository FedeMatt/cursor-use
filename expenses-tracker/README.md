# Expenses tracker

Generic pipeline: Cloudflare R2 PDF bills → cleaned markdown → HTML report.

Fork [cursor-use](https://github.com/FedeMatt/cursor-use), edit `config.toml` for your bucket and categories, then follow **Monthly automation** below.

## Layout

```
expenses-tracker/
  config.toml          # paths, categories, currency
  scripts/             # CLI entrypoints + cloud agent setup/trigger
  lib/                 # shared Python modules (+ agent_api client)
  assets/              # report CSS
  templates/           # cleaned markdown template
  skills/              # agent instructions (read these)
  .working/            # local draft files (gitignored)
  .agent-id            # durable cloud agent id (gitignored, from setup)
```

## Pipeline

1. Configure — [skills/config/SKILL.md](skills/config/SKILL.md)
2. `uv run expenses-tracker/scripts/process_bills.py`
3. Clean markdown — [skills/clean/SKILL.md](skills/clean/SKILL.md) + [skills/report/SKILL.md](skills/report/SKILL.md)
4. `uv run expenses-tracker/scripts/generate_report.py --force`
5. `uv run expenses-tracker/scripts/send_report.py` — optional, emails HTML report
6. No PR — outputs go to R2 (and inbox if email configured).

## Email (optional)

Skip manual PDF upload: deploy the [Email Worker](workers/email-ingest/) and forward your bank statement to it → R2. Receive the report by email via SMTP. See [skills/email/SKILL.md](skills/email/SKILL.md).

## Monthly automation

Two ways to run once per month:

| Method | Schedule | Setup |
|--------|----------|-------|
| **Cursor Automations** (dashboard) | Built-in cron | Create automation in UI, point at pipeline skill |
| **Cloud Agents API** | External cron | `setup_agent.py` once + GitHub Actions or manual trigger |

The [Cloud Agents API](https://cursor.com/docs/cloud-agent/api/endpoints) creates a durable agent (`bc-…`) and enqueues runs via `POST /v1/agents/{id}/runs`. It does **not** include scheduling — use `.github/workflows/monthly-expenses.yml` (1st of month, 09:00 UTC) or another cron.

```bash
# One-time: POST /v1/agents
export CURSOR_API_KEY="cursor_..." # pragma: allowlist secret
uv run expenses-tracker/scripts/setup_agent.py

# Monthly: POST /v1/agents/{id}/runs (or let GitHub Actions do it)
export EXPENSES_AGENT_ID="bc-..."   # optional if .agent-id exists
uv run expenses-tracker/scripts/trigger_monthly.py
```

Full details: [skills/automation-api/SKILL.md](skills/automation-api/SKILL.md).

## Skills (for agents)

| Skill | When to read |
|-------|----------------|
| [skills/pipeline/SKILL.md](skills/pipeline/SKILL.md) | Full automation workflow |
| [skills/automation-api/SKILL.md](skills/automation-api/SKILL.md) | API setup, GitHub Actions, secrets |
| [skills/email/SKILL.md](skills/email/SKILL.md) | Email PDF → R2, report → inbox |
| [skills/clean/SKILL.md](skills/clean/SKILL.md) | Cleaning OCR markdown |
| [skills/report/SKILL.md](skills/report/SKILL.md) | Statistics + HTML report specs |
| [skills/config/SKILL.md](skills/config/SKILL.md) | config.toml customization |

## Secrets

**Pipeline (local or cloud VM):** configure in `.env` or [Cloud Agents environment](https://cursor.com/docs/cloud-agent/environment):

- `R2_ACCOUNT_ID` / `ACCOUNT_ID`
- `R2_ACCESS_KEY_ID` / `ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY` / `SECRET_ACCESS_KEY`
- `R2_BUCKET` / `BUCKET_NAME` — your R2 bucket name

**API automation:** add as GitHub repository secrets (for the monthly workflow):

- `CURSOR_API_KEY` — [Dashboard → Integrations](https://cursor.com/dashboard/integrations)
- `EXPENSES_AGENT_ID` — `bc-…` from `setup_agent.py`

**Report email (optional):** `REPORT_EMAIL_TO`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` — see [skills/email/SKILL.md](skills/email/SKILL.md).
