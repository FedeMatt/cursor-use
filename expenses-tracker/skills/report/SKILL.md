---
name: expenses-tracker-report
description: Defines agent-authored key statistics for the expenses HTML report — avg daily spending, highest transaction, top category, insight notes. Use when filling the # Statistics section in cleaned markdown or when generating the monthly expense report.
---

# Report statistics (agent step)

Section **02 Key Statistics** in the HTML report comes from the `# Statistics` table in cleaned markdown. **You** verify and refine these values during the clean step.

## When to run

After `clean_markdown.py draft`, before `push`. The draft pre-fills computed values — your job is to verify accuracy and add narrative context.

## Required metrics

Add or verify every row in `# Statistics`:

| metric | Description | How to compute |
|--------|-------------|----------------|
| `avg_daily_spending` | Mean spend per day with activity | `purchases_debits ÷ spending_days`, or sum of debits ÷ unique post dates |
| `highest_transaction` | Largest single debit | Max amount from transaction table |
| `highest_merchant` | Merchant of largest debit | Description field of that row |
| `lowest_transaction` | Smallest debit (exclude $0 fees if noise) | Min debit amount |
| `lowest_merchant` | Merchant of smallest debit | Description of min row |
| `avg_transaction` | Mean debit amount | Total debits ÷ debit count |
| `spending_days` | Days with at least one debit | Count unique `post_date` values |
| `top_category` | Category with highest total | From config.toml keyword rules |
| `top_category_amount` | Total spent in top category | Sum of debits in that category |

## Narrative insight (required)

Add one line after the statistics table:

```
insight_note: Groceries and dining made up 60% of spend; transport stayed flat vs last month.
```

Write 1–2 sentences the account holder would find useful — patterns, outliers, category shifts. Do not repeat raw numbers already in the table.

## Example

```markdown
# Statistics

| metric | value |
| --- | --- |
| avg_daily_spending | 51.27 |
| highest_transaction | 144.00 |
| highest_merchant | LOTTE DUTY FREE-T2 |
| lowest_transaction | 0.41 |
| lowest_merchant | DCC FEE |
| avg_transaction | 25.49 |
| spending_days | 28 |
| top_category | Groceries |
| top_category_amount | 389.86 |

insight_note: Duty-free shopping was the single largest purchase; everyday groceries still led by category total.
```

## HTML mapping

| Report section | Source |
|----------------|--------|
| Hero Total Due | frontmatter `total_due` |
| 01 Spending by Category | parsed transactions + config.toml |
| 02 Key Statistics | `# Statistics` table (+ `insight_note`) |
| 03 Transactions | `# Transactions` table |

## Validation

`clean_markdown.py push` fails if any required metric is missing. Fix the table and retry.

## After push

```bash
uv run expenses-tracker/scripts/generate_report.py --force
```

Confirm section 02 shows your stats and insight note in the downloaded HTML.
