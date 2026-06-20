"""Load expenses-tracker config from TOML (stdlib tomllib)."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PKG_ROOT / "config.toml"


@dataclass(frozen=True)
class Category:
    name: str
    color: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    source_prefix: str
    markdown_prefix: str
    reports_prefix: str
    report_title: str
    report_eyebrow: str
    currency_symbol: str
    currency_code: str
    default_category: str
    date_re: re.Pattern[str]
    amount_re: re.Pattern[str]
    credit_suffix: str
    total_due_re: re.Pattern[str]
    period_re: re.Pattern[str]
    categories: tuple[Category, ...]


def _path(raw: dict, key: str, env_key: str, default: str) -> str:
    return os.environ.get(env_key) or raw.get("paths", {}).get(key, default)


def load_config(path: Path | None = None) -> Config:
    cfg_path = Path(os.environ.get("EXPENSES_CONFIG", path or DEFAULT_CONFIG))
    raw = tomllib.loads(cfg_path.read_text())
    report = raw.get("report", {})
    parse = raw.get("parse", {})
    cats = [
        Category(
            name=c["name"],
            color=c.get("color", "#DA7756"),
            keywords=tuple(k.lower() for k in c.get("keywords", [])),
        )
        for c in raw.get("categories", [])
    ]
    return Config(
        source_prefix=_path(
            raw, "source_pdfs", "R2_SOURCE_PREFIX", "credit-card-bills/"
        ),
        markdown_prefix=_path(raw, "markdown", "R2_DEST_PREFIX", "monthly-expense/"),
        reports_prefix=_path(raw, "reports", "R2_REPORTS_PREFIX", "monthly-reports/"),
        report_title=report.get("title", "Monthly Expense Report"),
        report_eyebrow=report.get("eyebrow", "Personal Finance — Statement"),
        currency_symbol=report.get("currency_symbol", "$"),
        currency_code=report.get("currency_code", "USD"),
        default_category=report.get("default_category", "Etc."),
        date_re=re.compile(parse.get("date", r"^\s*\d{1,2}\s*\w{3}"), re.I),
        amount_re=re.compile(parse.get("amount", r"^[\d,]+\.\d{2}(?:CR)?$"), re.I),
        credit_suffix=parse.get("credit_suffix", "CR"),
        total_due_re=re.compile(
            parse.get("total_due", r"Total Due\s+([\d,]+\.\d{2})"), re.I
        ),
        period_re=re.compile(
            parse.get(
                "period",
                r"From\s+(\d{1,2}\s+\w{3}\s+\d{4})\s+to\s+(\d{1,2}\s+\w{3}\s+\d{4})",
            ),
            re.I,
        ),
        categories=tuple(cats),
    )
