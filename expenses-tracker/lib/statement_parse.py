"""Parse statement metadata and frontmatter from raw or cleaned markdown."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from config import Config

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(md: str) -> dict[str, str]:
    m = _FRONTMATTER.match(md)
    if not m:
        return {}
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def _first_group(patterns: list[re.Pattern[str]], text: str) -> str | None:
    for pat in patterns:
        if m := pat.search(text):
            return m.group(1)
    return None


def _normalize_amount(value: str) -> str:
    return value.replace(",", "").strip()


def parse_meta(md: str, cfg: Config) -> dict[str, str]:
    meta = parse_frontmatter(md)

    fallbacks = [
        re.compile(r"Total\s*Due[^\d]{0,40}([\d,]+\.\d{2})", re.I),
        re.compile(r"\|\s*Total\s*Due\s*\|\s*([\d,]+\.\d{2})", re.I),
        cfg.total_due_re,
    ]
    balance_fallbacks = [
        re.compile(r"Total\s*Account\s*Balance[^\d]{0,40}([\d,]+\.\d{2})", re.I),
        re.compile(r"\|\s*Total\s*Account\s*Balance\s*\|\s*([\d,]+\.\d{2})", re.I),
    ]
    min_pay_fallbacks = [
        re.compile(r"Minimum\s*Payment[^\d]{0,40}([\d,]+\.\d{2})", re.I),
    ]
    purchases_fallbacks = [
        re.compile(r"Purchases\s*(?:&|and)\s*Debits[^\d]{0,40}([\d,]+\.\d{2})", re.I),
    ]
    payments_fallbacks = [
        re.compile(r"Payments\s*(?:&|and)\s*Credits[^\d]{0,40}([\d,]+\.\d{2})", re.I),
    ]
    prev_fallbacks = [
        re.compile(r"Previous\s*Statement\s*Balance[^\d]{0,40}([\d,]+\.\d{2})", re.I),
    ]

    if not meta.get("total_due") and (v := _first_group(fallbacks, md)):
        meta["total_due"] = v
    if not meta.get("total_account_balance") and (
        v := _first_group(balance_fallbacks, md)
    ):
        meta["total_account_balance"] = v
    if not meta.get("minimum_payment") and (v := _first_group(min_pay_fallbacks, md)):
        meta["minimum_payment"] = v
    if not meta.get("purchases_debits") and (
        v := _first_group(purchases_fallbacks, md)
    ):
        meta["purchases_debits"] = v
    if not meta.get("payments_credits") and (v := _first_group(payments_fallbacks, md)):
        meta["payments_credits"] = v
    if not meta.get("previous_balance") and (v := _first_group(prev_fallbacks, md)):
        meta["previous_balance"] = v

    if not meta.get("period_start") or not meta.get("period_end"):
        if m := cfg.period_re.search(md):
            meta.setdefault("period_start", m.group(1))
            meta.setdefault("period_end", m.group(2))
        elif period := meta.get("statement_period"):
            if m := re.search(
                r"(\d{1,2}\s+\w{3}\s+\d{4})\s+to\s+(\d{1,2}\s+\w{3}\s+\d{4})",
                period,
                re.I,
            ):
                meta.setdefault("period_start", m.group(1))
                meta.setdefault("period_end", m.group(2))

    for key in (
        "total_due",
        "total_account_balance",
        "minimum_payment",
        "purchases_debits",
        "payments_credits",
        "previous_balance",
    ):
        if key in meta:
            meta[key] = _normalize_amount(meta[key])

    return meta


def cleaned_r2_key(raw_key: str) -> str:
    p = PurePosixPath(raw_key)
    return str(p.with_name(f"{p.stem}.cleaned.md"))
