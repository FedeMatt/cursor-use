---
name: expenses-tracker
description: Runs a generic monthly expenses pipeline — PDF bills in Cloudflare R2 to cleaned markdown with agent statistics, then HTML report. Use when running the expenses-tracker automation or generating monthly expense reports from R2.
---

# Expenses tracker pipeline

See [../README.md](../README.md) for repo layout.

## Steps

```bash
uv sync
uv run expenses-tracker/scripts/process_bills.py
uv run expenses-tracker/scripts/clean_markdown.py draft
# Agent: edit .working/statement.cleaned.md — see skills/clean/ and skills/report/
uv run expenses-tracker/scripts/clean_markdown.py push
uv run expenses-tracker/scripts/generate_report.py --force
uv run expenses-tracker/scripts/send_report.py   # optional — if REPORT_EMAIL_TO is set
```

Do **not** open a pull request.

## Email (optional)

- **Inbound PDF** — forward statement to a Cloudflare Email Worker → R2. See [skills/email/SKILL.md](../email/SKILL.md). Email the PDF **before** running this pipeline.
- **Outbound report** — `send_report.py` emails the HTML report after generation (R2 upload still happens).

## Agent responsibilities

1. **Clean** — [skills/clean/SKILL.md](../clean/SKILL.md): frontmatter totals, transaction table
2. **Statistics** — [skills/report/SKILL.md](../report/SKILL.md): `# Statistics` table + `insight_note`
3. **Report** — `generate_report.py` renders HTML section 02 from agent stats

## Automation prompt

```
You are the monthly expenses-tracker agent.

1. uv sync
2. uv run expenses-tracker/scripts/process_bills.py
3. uv run expenses-tracker/scripts/clean_markdown.py draft
4. Edit expenses-tracker/.working/statement.cleaned.md:
   - Verify frontmatter totals against raw statement
   - Verify/refine # Statistics (see skills/report/SKILL.md)
   - Add insight_note (1–2 sentences on spending patterns)
5. uv run expenses-tracker/scripts/clean_markdown.py push
6. uv run expenses-tracker/scripts/generate_report.py --force
7. uv run expenses-tracker/scripts/send_report.py   # if email configured
8. Summarize: total due, key stats, top category, report R2 key
9. Do NOT open a pull request
```

## Scheduling

- **Cursor Automations UI** — built-in monthly cron (no code)
- **Cloud Agents API** — [skills/automation-api/SKILL.md](../automation-api/SKILL.md): `setup_agent.py` once, GitHub Actions cron triggers `trigger_monthly.py`

The API has no native schedule; pair it with `.github/workflows/monthly-expenses.yml` or another cron.

## Troubleshooting

| Issue | Skill |
|-------|-------|
| Wrong totals | skills/clean/SKILL.md |
| Missing stats section | skills/report/SKILL.md |
| Wrong categories | skills/config/SKILL.md |
| API / monthly trigger | skills/automation-api/SKILL.md |
| Email PDF in / report out | skills/email/SKILL.md |
