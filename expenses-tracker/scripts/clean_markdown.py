"""Pull raw statement markdown for agent cleaning; push cleaned version back to R2."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from config import load_config
from r2_util import (
    bucket_name,
    is_current_month,
    list_objects,
    load_dotenv,
    r2_client,
    read_object,
    write_object,
)
from statement_parse import cleaned_r2_key, parse_frontmatter, parse_meta
from statistics import (
    compute_statistics,
    format_statistics_section,
    validate_statistics,
)
from transactions import parse_transactions

PKG_ROOT = Path(__file__).resolve().parents[1]
WORKING = PKG_ROOT / ".working"
RAW_LOCAL = WORKING / "statement.raw.md"
CLEANED_LOCAL = WORKING / "statement.cleaned.md"

_REQUIRED_FRONTMATTER = (
    "statement_period",
    "total_due",
    "total_account_balance",
)
_REQUIRED_TABLE_HEADER = "| post_date | trans_date | description | location | amount |"


def _current_raw_key(client, bucket: str, markdown_prefix: str) -> str | None:
    candidates = [
        (key, modified)
        for key, modified in list_objects(client, bucket, markdown_prefix)
        if key.lower().endswith(".md")
        and not key.lower().endswith(".cleaned.md")
        and is_current_month(modified)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[1])[0]


def pull(*, cfg=None) -> str:
    cfg = cfg or load_config()
    client = r2_client()
    bucket = bucket_name()
    key = _current_raw_key(client, bucket, cfg.markdown_prefix)
    if not key:
        raise SystemExit("no current-month raw markdown found in R2")

    WORKING.mkdir(parents=True, exist_ok=True)
    RAW_LOCAL.write_text(read_object(client, bucket, key), encoding="utf-8")
    cleaned_key = cleaned_r2_key(key)
    print(key)
    print(RAW_LOCAL)
    print(cleaned_key)
    return key


def draft(*, cfg=None) -> str:
    """Pre-fill cleaned markdown — agent verifies totals, stats, and insight_note."""
    cfg = cfg or load_config()
    pull(cfg=cfg)
    raw = RAW_LOCAL.read_text(encoding="utf-8")
    meta = parse_meta(raw, cfg)
    df = parse_transactions(raw, cfg)
    stats = compute_statistics(df, meta, cfg)

    period = meta.get("statement_period") or (
        f"{meta.get('period_start', '')} to {meta.get('period_end', '')}".strip()
    )
    lines = ["---", f"statement_period: {period}"]
    for key in (
        "total_due",
        "total_account_balance",
        "minimum_payment",
        "payment_due_date",
        "previous_balance",
        "payments_credits",
        "purchases_debits",
    ):
        if meta.get(key):
            lines.append(f"{key}: {meta[key]}")
    lines.extend([f"currency: {cfg.currency_code}", "---", ""])
    lines.extend(format_statistics_section(stats))
    lines.extend(
        [
            "",
            "# Transactions",
            "",
            "| post_date | trans_date | description | location | amount |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for r in df.itertuples():
        amt = f"{r.amount:,.2f}"
        if r.kind == "credit":
            amt += cfg.credit_suffix
        loc = r.location.replace("|", " ")
        desc = r.description.replace("|", " ")
        lines.append(f"| {r.post_date} | {r.trans_date} | {desc} | {loc} | {amt} |")

    CLEANED_LOCAL.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(CLEANED_LOCAL)
    print("Review frontmatter, # Statistics, add insight_note, then: push")
    return str(CLEANED_LOCAL)


def _validate_cleaned(text: str) -> list[str]:
    errors: list[str] = []
    fm = parse_frontmatter(text)
    if not fm:
        errors.append("missing YAML frontmatter (must start with ---)")
    for field in _REQUIRED_FRONTMATTER:
        if field not in fm or not str(fm[field]).strip():
            errors.append(f"frontmatter missing: {field}")
    if _REQUIRED_TABLE_HEADER.lower() not in text.lower():
        errors.append(f"missing transactions table header: {_REQUIRED_TABLE_HEADER}")
    tx_lines = [
        ln
        for ln in text.splitlines()
        if ln.startswith("|") and re.search(r"[\d,]+\.\d{2}", ln)
    ]
    if len(tx_lines) < 1:
        errors.append("transactions table appears empty")
    if "picture [" in text.lower() or "intentionally omitted" in text.lower():
        errors.append("still contains OCR picture placeholders — remove them")
    errors.extend(validate_statistics(text))
    if "insight_note:" not in text.lower():
        errors.append("missing insight_note (one-line summary after # Statistics)")
    return errors


def push(*, cfg=None, force: bool = False) -> str:
    cfg = cfg or load_config()
    if not CLEANED_LOCAL.is_file():
        raise SystemExit(f"cleaned file not found: {CLEANED_LOCAL}")

    text = CLEANED_LOCAL.read_text(encoding="utf-8")
    errors = _validate_cleaned(text)
    if errors:
        for err in errors:
            print(f"validation error: {err}", file=sys.stderr)
        raise SystemExit(1)

    client = r2_client()
    bucket = bucket_name()
    raw_key = _current_raw_key(client, bucket, cfg.markdown_prefix)
    if not raw_key:
        raise SystemExit("no current-month raw markdown found in R2")

    dest = cleaned_r2_key(raw_key)
    if not force and dest in {
        k for k, _ in list_objects(client, bucket, cfg.markdown_prefix)
    }:
        print(dest)
        return dest

    write_object(client, bucket, dest, text, "text/markdown; charset=utf-8")
    print(dest)
    return dest


def status(*, cfg=None) -> None:
    cfg = cfg or load_config()
    client = r2_client()
    bucket = bucket_name()
    raw = _current_raw_key(client, bucket, cfg.markdown_prefix)
    if not raw:
        print("raw: none")
        return
    cleaned = cleaned_r2_key(raw)
    keys = {k for k, _ in list_objects(client, bucket, cfg.markdown_prefix)}
    print(f"raw: {raw}")
    print(f"cleaned: {cleaned} ({'yes' if cleaned in keys else 'no'})")
    print(f"local raw: {RAW_LOCAL} ({'yes' if RAW_LOCAL.is_file() else 'no'})")
    print(
        f"local cleaned: {CLEANED_LOCAL} ({'yes' if CLEANED_LOCAL.is_file() else 'no'})"
    )


def _self_check() -> None:
    sample = """---
statement_period: 19 MAY 2026 to 18 JUN 2026
total_due: 1317.21
total_account_balance: 1317.21
minimum_payment: 50.00
---

# Statistics
| metric | value |
| --- | --- |
| avg_daily_spending | 10.00 |
| highest_transaction | 50.00 |
| highest_merchant | Foo |
| lowest_transaction | 1.00 |
| lowest_merchant | Bar |
| avg_transaction | 5.00 |
| spending_days | 3 |
| top_category | Groceries |
| top_category_amount | 30.00 |

insight_note: Sample insight for self-check.

# Transactions
| post_date | trans_date | description | location | amount |
| --- | --- | --- | --- | --- |
| 22 May | 22May | Grab trip | Singapore | 22.40 |
"""
    assert not _validate_cleaned(sample)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["pull", "draft", "push", "status"], nargs="?"
    )
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        _self_check()
        print("self-check ok")
    elif args.command == "pull":
        pull()
    elif args.command == "draft":
        draft()
    elif args.command == "push":
        push(force=args.force)
    elif args.command == "status":
        status()
    else:
        parser.print_help()
        sys.exit(1)
