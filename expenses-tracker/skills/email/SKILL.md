---
name: expenses-tracker-email
description: Email bank statement PDFs into R2 via Cloudflare Email Worker, and receive the HTML expense report by email. Use when setting up email ingestion instead of manual R2 upload, or outbound report delivery.
---

# Email in / out

Two separate pieces — neither is a Cursor Automation:

| Direction | What | Where it runs |
|-----------|------|----------------|
| **In** | PDF attachment → R2 `credit-card-bills/` | Cloudflare Email Worker |
| **Out** | HTML report → your inbox | `send_report.py` at end of pipeline |

The Cursor agent still runs the normal pipeline; it just skips manual PDF upload.

## Flow

```
You email PDF ──► Email Worker ──► R2 credit-card-bills/
                                        │
Cursor automation ◄─────────────────────┘
  process_bills → clean → report → R2 monthly-reports/
                                        │
send_report.py ─────────────────────────┘──► your inbox
```

**Order matters:** email the statement **before** triggering the automation (or ensure your monthly cron runs after the bank usually sends the bill).

---

## 1. Inbound — statement PDF via email

Deploy `expenses-tracker/workers/email-ingest/`:

```bash
cd expenses-tracker/workers/email-ingest
# Edit wrangler.toml: bucket_name, R2_PREFIX, ALLOWED_FROM
npm install
npx wrangler deploy
```

In **Cloudflare → Email Routing → Routing rules**:

- Address: `bills@yourdomain.com` (or any alias on your zone)
- Action: **Send to a Worker** → `expenses-email-ingest`

When you receive your bank statement, **forward or send it** to that address with the PDF attached. The worker:

- Accepts only `.pdf` attachments
- Optionally filters by envelope sender (`ALLOWED_FROM` in `wrangler.toml`)
- Writes to `{R2_PREFIX}{YYYY-MM-DD}_{filename}.pdf`

No Cursor involvement — this is always-on Cloudflare infrastructure.

### Security

- Set `ALLOWED_FROM` to your email and/or the bank's notification address
- Use a dedicated subdomain for routing (e.g. `bills.yourdomain.com`)

---

## 2. Outbound — report to your inbox

Add to `.env` (local) or **Cloud Agents environment** (automation). Copy from [`env.example`](../../env.example).

### Gmail

1. Enable 2FA on your Google account.
2. Create an [App Password](https://myaccount.google.com/apppasswords) (Mail → Other → "expenses-tracker").
3. Add to `.env` — **do not paste the password in chat or commit it to git**:

```bash
REPORT_EMAIL_TO=you@gmail.com
REPORT_EMAIL_FROM=you@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # 16-char app password (spaces optional)
```

4. Test locally (after a report exists in R2):

```bash
uv run expenses-tracker/scripts/send_report.py --dry-run
uv run expenses-tracker/scripts/send_report.py
```

| Variable | Example |
|----------|---------|
| `REPORT_EMAIL_TO` | `you@gmail.com` |
| `REPORT_EMAIL_FROM` | optional; defaults to `SMTP_USER` |
| `REPORT_EMAIL_SUBJECT` | optional override |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | your Gmail address |
| `SMTP_PASSWORD` | Google app password (not your login password) |

---

## 3. Pipeline + automation

Add to the agent prompt (after `generate_report.py`):

```bash
uv run expenses-tracker/scripts/send_report.py
```

Full pipeline with email:

```bash
uv sync
uv run expenses-tracker/scripts/process_bills.py
uv run expenses-tracker/scripts/clean_markdown.py draft
# agent edits .working/statement.cleaned.md
uv run expenses-tracker/scripts/clean_markdown.py push
uv run expenses-tracker/scripts/generate_report.py --force
uv run expenses-tracker/scripts/send_report.py
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Worker rejects email | Check `ALLOWED_FROM`; ensure PDF is attached |
| `nothing to process` | PDF must land in R2 before automation runs; check bucket prefix |
| `report not found` | Run `generate_report.py --force` before `send_report.py` |
| SMTP auth fails | Use an app-specific password; port 587 + STARTTLS |
