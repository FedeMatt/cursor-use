"""Agent-authored statistics from cleaned markdown, with computed fallbacks."""

from __future__ import annotations


import pandas as pd

from config import Config

REQUIRED_STATS = (
    "avg_daily_spending",
    "highest_transaction",
    "highest_merchant",
    "lowest_transaction",
    "lowest_merchant",
    "avg_transaction",
    "spending_days",
    "top_category",
    "top_category_amount",
)

STAT_LABELS: dict[str, str] = {
    "avg_daily_spending": "Average daily spending",
    "highest_transaction": "Highest transaction",
    "highest_merchant": "Highest merchant",
    "lowest_transaction": "Lowest transaction",
    "lowest_merchant": "Lowest merchant",
    "avg_transaction": "Average transaction",
    "spending_days": "Days with spending",
    "top_category": "Top category",
    "top_category_amount": "Top category spend",
}

_STATISTICS_HEADER = "| metric | value |"


def parse_statistics(md: str) -> dict[str, str]:
    """Read agent-authored # Statistics table and insight_note from cleaned markdown."""
    stats: dict[str, str] = {}
    in_section = False
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("insight_note:"):
            stats["insight_note"] = stripped.split(":", 1)[1].strip().strip('"')
            continue
        if stripped.lower() == "# statistics":
            in_section = True
            continue
        if in_section and line.startswith("#"):
            break
        if not in_section or not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2 or cols[0].lower() in ("metric", "---"):
            continue
        stats[cols[0]] = cols[1]
    return stats


def compute_statistics(
    df: pd.DataFrame, meta: dict[str, str], cfg: Config
) -> dict[str, str]:
    debits = df[df["kind"] == "debit"] if not df.empty else df
    if debits.empty:
        return {}

    spending_days = int(debits["post_date"].nunique())
    total = float(debits["amount"].sum())
    avg_daily = total / spending_days if spending_days else 0.0
    avg_tx = total / len(debits) if len(debits) else 0.0

    hi = debits.loc[debits["amount"].idxmax()]
    lo = debits.loc[debits["amount"].idxmin()]
    by_cat = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    top_cat = by_cat.index[0]
    top_amt = float(by_cat.iloc[0])

    if meta.get("purchases_debits"):
        try:
            avg_daily = float(meta["purchases_debits"]) / spending_days
        except (ValueError, ZeroDivisionError):
            pass

    return {
        "avg_daily_spending": f"{avg_daily:.2f}",
        "highest_transaction": f"{float(hi['amount']):.2f}",
        "highest_merchant": str(hi["description"]),
        "lowest_transaction": f"{float(lo['amount']):.2f}",
        "lowest_merchant": str(lo["description"]),
        "avg_transaction": f"{avg_tx:.2f}",
        "spending_days": str(spending_days),
        "top_category": str(top_cat),
        "top_category_amount": f"{top_amt:.2f}",
    }


def resolve_statistics(
    md: str, df: pd.DataFrame, meta: dict[str, str], cfg: Config
) -> dict[str, str]:
    """Agent stats override computed fallbacks."""
    computed = compute_statistics(df, meta, cfg)
    agent = parse_statistics(md)
    return {**computed, **agent}


def format_statistics_section(stats: dict[str, str]) -> list[str]:
    lines = [
        "# Statistics",
        "",
        "Review and refine these values before push. Agent-authored values appear in the HTML report.",
        "",
        _STATISTICS_HEADER,
        "| --- | --- |",
    ]
    for key in REQUIRED_STATS:
        if key in stats:
            lines.append(f"| {key} | {stats[key]} |")
    note = stats.get("insight_note", "").strip()
    if note:
        lines.extend(["", f"insight_note: {note}"])
    return lines


def validate_statistics(md: str) -> list[str]:
    stats = parse_statistics(md)
    errors: list[str] = []
    if _STATISTICS_HEADER.lower() not in md.lower():
        errors.append("missing # Statistics section")
    for key in REQUIRED_STATS:
        if key not in stats or not str(stats[key]).strip():
            errors.append(f"statistics missing: {key}")
    return errors


def _self_check() -> None:
    md = """
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
"""
    stats = parse_statistics(md)
    assert stats["avg_daily_spending"] == "10.00"
    assert not validate_statistics(md)
