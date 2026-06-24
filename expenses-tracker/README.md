# Expenses tracker

**PDF bank statement in → HTML expense report out.**  
A Cursor cloud agent reads your bill from R2, cleans OCR noise, verifies statistics, and publishes a dark ledger-style report — no pull request, no manual spreadsheet.

<p align="center">
  <img src="assets/report-screenshot.png" alt="Monthly expense report — category breakdown, total due, and key statistics" width="720">
</p>

<p align="center">
  <em>Sample output: categories, agent-verified stats, statement totals.</em>
</p>

Fork this repo, edit [`config.toml`](config.toml) for your merchants and R2 bucket, and run it locally or on a monthly Cursor automation.

---

## What you get

| | |
|---|---|
| **Input** | Credit-card PDF (upload to R2, or forward by email) |
| **Agent step** | Cleans markdown, verifies totals, writes spending insights |
| **Output** | HTML report in R2 — optionally emailed to your inbox |
| **Schedule** | Manual, Cursor Automations cron, or GitHub Actions + Cloud Agents API |

---

## Quick start

```bash
uv sync
uv run expenses-tracker/scripts/process_bills.py
uv run expenses-tracker/scripts/clean_markdown.py draft   # agent edits .working/
uv run expenses-tracker/scripts/clean_markdown.py push
uv run expenses-tracker/scripts/generate_report.py --force
uv run expenses-tracker/scripts/send_report.py             # optional
```

Configure R2 paths, categories, and currency in [`config.toml`](config.toml) — see [skills/config/SKILL.md](skills/config/SKILL.md).

---

## Optional: email instead of manual upload

**Inbound** — forward your bank PDF to `bills@yourdomain.com`; a [Cloudflare Email Worker](workers/email-ingest/) saves it to R2.

**Outbound** — `send_report.py` emails the HTML report via Gmail SMTP.

Full setup: [skills/email/SKILL.md](skills/email/SKILL.md).

---

## Monthly automation

| Method | Schedule | Setup |
|--------|----------|-------|
| **Cursor Automations** | Built-in cron | Point automation at [skills/pipeline/SKILL.md](skills/pipeline/SKILL.md) |
| **Cloud Agents API** | GitHub Actions | `setup_agent.py` once → `trigger_monthly.py` each month |

```bash
export CURSOR_API_KEY="cursor_..." # pragma: allowlist secret
uv run expenses-tracker/scripts/setup_agent.py
uv run expenses-tracker/scripts/trigger_monthly.py
```

Details: [skills/automation-api/SKILL.md](skills/automation-api/SKILL.md) · workflow: [`.github/workflows/monthly-expenses.yml`](../.github/workflows/monthly-expenses.yml)

---

## Layout

```
expenses-tracker/
  config.toml              # your bucket, categories, currency
  scripts/                 # pipeline + cloud agent + email
  lib/                     # R2, parsing, HTML, report keys
  assets/                  # report.css + screenshots
  workers/email-ingest/    # PDF → R2 via email
  skills/                  # agent instructions
  templates/               # cleaned markdown shape
```

---

## Skills (for agents)

| Skill | When to read |
|-------|----------------|
| [skills/pipeline/SKILL.md](skills/pipeline/SKILL.md) | Full automation workflow |
| [skills/email/SKILL.md](skills/email/SKILL.md) | Email PDF in, report out |
| [skills/automation-api/SKILL.md](skills/automation-api/SKILL.md) | API + GitHub Actions |
| [skills/clean/SKILL.md](skills/clean/SKILL.md) | Cleaning OCR markdown |
| [skills/report/SKILL.md](skills/report/SKILL.md) | Statistics + HTML specs |
| [skills/config/SKILL.md](skills/config/SKILL.md) | config.toml customization |

---

## Secrets

**R2** (`.env` or [Cloud Agents environment](https://cursor.com/docs/cloud-agent/environment)):

`R2_ACCOUNT_ID` · `R2_ACCESS_KEY_ID` · `R2_SECRET_ACCESS_KEY` · `R2_BUCKET`

**API automation** (GitHub secrets): `CURSOR_API_KEY` · `EXPENSES_AGENT_ID`

**Report email** (optional): `REPORT_EMAIL_TO` · `SMTP_*` — see [skills/email/SKILL.md](skills/email/SKILL.md)

Copy placeholders from [`env.example`](../.env.example).
