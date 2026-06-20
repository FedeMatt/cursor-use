"""Parse and categorize transactions from statement markdown tables."""

from __future__ import annotations

import re

import pandas as pd

from config import Config


def _clean_cell(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"~~|_{2,}", "", text)
    return " ".join(text.split()).strip()


def _parse_amount(raw: str, cfg: Config) -> tuple[float, str]:
    raw = raw.replace(",", "").strip()
    suffix = cfg.credit_suffix.upper()
    if raw.upper().endswith(suffix):
        return float(raw[: -len(suffix)]), "credit"
    return float(raw), "debit"


def categorize(description: str, location: str, cfg: Config) -> str:
    hay = f"{description} {location}".lower()
    for cat in cfg.categories:
        if any(k in hay for k in cat.keywords):
            return cat.name
    return cfg.default_category


def parse_transactions(md: str, cfg: Config) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for line in md.splitlines():
        if not line.startswith("|") or line.count("|") < 5:
            continue
        cols = [_clean_cell(c) for c in line.strip("|").split("|")]
        if len(cols) < 5:
            continue
        post_date, trans_date, description, location, amount_raw = cols[:5]
        if cols[0].lower() == "post_date" or cols[0].lower() == "metric":
            continue
        if not cfg.date_re.match(post_date) or not cfg.amount_re.match(amount_raw):
            continue
        amount, kind = _parse_amount(amount_raw, cfg)
        rows.append(
            {
                "post_date": post_date,
                "trans_date": trans_date,
                "description": description,
                "location": location,
                "amount": amount,
                "kind": kind,
                "category": categorize(description, location, cfg),
            }
        )
    return pd.DataFrame(rows)
