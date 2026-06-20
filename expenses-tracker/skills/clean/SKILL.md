---
name: expenses-tracker-clean
description: Cleans noisy OCR credit-card statement markdown into structured frontmatter, statistics table, and transaction rows before report generation. Use after process_bills.py when markdown contains disclaimers, picture placeholders, or buried statement totals.
---

# Clean statement markdown

Raw OCR markdown is noisy. Normalize it into the format in `templates/cleaned-statement.template.md`.

## Workflow

```bash
uv run expenses-tracker/scripts/clean_markdown.py draft
# Edit expenses-tracker/.working/statement.cleaned.md
uv run expenses-tracker/scripts/clean_markdown.py push
```

Files: `.working/statement.raw.md` (read-only reference), `.working/statement.cleaned.md` (you edit).

## Required sections

### 1. YAML frontmatter

- `statement_period`, `total_due`, `total_account_balance` (required)
- Recommended: `minimum_payment`, `payment_due_date`, `previous_balance`, `payments_credits`, `purchases_debits`, `currency`

Copy totals from the **statement summary**, not by summing transactions.

### 2. `# Statistics`

See [skills/report/SKILL.md](../report/SKILL.md). Required before `push`.

### 3. `# Transactions`

Header: `| post_date | trans_date | description | location | amount |`

Include every transaction; credits use `CR` suffix.

## Remove

- Legal disclaimers, rate tables, payment instructions
- `picture [...] intentionally omitted` blocks
- Non-transaction OCR noise

## Checklist

- [ ] Frontmatter totals match statement PDF
- [ ] `# Statistics` complete (agent verified)
- [ ] `insight_note` added
- [ ] All transactions present
- [ ] `push` succeeds
