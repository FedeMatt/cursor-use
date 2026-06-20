---
name: expenses-tracker-config
description: Configures the expenses-tracker pipeline — R2 paths, merchant category rules, HTML report labels, and parse patterns. Use when customizing config.toml, adding expense categories, tuning keyword matching, or adjusting report currency and styling for a new user or bank statement format.
---

# Expenses tracker — configuration

All user-specific settings live in **`expenses-tracker/config.toml`**.

Point to a custom file with `EXPENSES_CONFIG=/path/to/config.toml`.

See [skills/pipeline/SKILL.md](../pipeline/SKILL.md) for the full workflow.

## Quick setup

1. Create a Cloudflare R2 bucket and [API token](https://developers.cloudflare.com/r2/api/tokens/) with Object Read & Write.
2. Add secrets (see pipeline skill).
3. Edit `config.toml`: `[paths]`, `[report]`, `[[categories]]`.
4. Upload PDF bills to `{source_pdfs}`.

## `[paths]`

| Key | Default | Env override |
|-----|---------|--------------|
| `source_pdfs` | `credit-card-bills/` | `R2_SOURCE_PREFIX` |
| `markdown` | `monthly-expense/` | `R2_DEST_PREFIX` |
| `reports` | `monthly-reports/` | `R2_REPORTS_PREFIX` |

## `[report]`

| Key | Purpose |
|-----|---------|
| `title` | H1 in HTML masthead |
| `eyebrow` | Small label above title |
| `currency_symbol` | Display prefix |
| `currency_code` | Footnote label |
| `default_category` | Fallback category name |

## `[[categories]]`

```toml
[[categories]]
name = "Groceries"
color = "#E8B49C"
keywords = ["fairprice", "whole foods"]
```

First keyword match wins. Unmatched → `default_category`.

## Validation

```bash
uv run expenses-tracker/scripts/generate_report.py --self-check
```
