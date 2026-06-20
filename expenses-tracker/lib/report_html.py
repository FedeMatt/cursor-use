"""Render the dark ledger-style HTML expense report."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import Config
from statistics import STAT_LABELS

PKG_ROOT = Path(__file__).resolve().parents[1]
_CSS = (PKG_ROOT / "assets" / "report.css").read_text()
_PALETTE = ("#DA7756", "#E8B49C", "#7FA882", "#9C968D", "#C97B63", "#5B5651")

# Keys shown in section 02, in display order
_DISPLAY_STATS = (
    "avg_daily_spending",
    "highest_transaction",
    "highest_merchant",
    "lowest_transaction",
    "avg_transaction",
    "spending_days",
    "top_category",
    "top_category_amount",
)


def _money_parts(amount: float, symbol: str) -> tuple[str, str]:
    whole, cents = divmod(round(amount * 100), 100)
    return f"{symbol}{whole:,}", f".{cents:02d}"


def _fmt(amount: float, symbol: str) -> str:
    return f"{symbol}{amount:,.2f}"


def _category_colors(cfg: Config, categories: list[str]) -> dict[str, str]:
    from_config = {c.name: c.color for c in cfg.categories}
    colors: dict[str, str] = {}
    fallback_i = 0
    for name in categories:
        if name in from_config:
            colors[name] = from_config[name]
        elif name == cfg.default_category:
            colors[name] = "#5B5651"
        else:
            colors[name] = _PALETTE[fallback_i % len(_PALETTE)]
            fallback_i += 1
    return colors


def _ledger_rows(
    by_cat: pd.DataFrame, total: float, colors: dict[str, str], symbol: str
) -> str:
    if by_cat.empty:
        return '<div class="ledger-row"><span class="cat-name">No spending parsed</span></div>'
    max_amt = float(by_cat["amount"].max())
    rows = []
    for r in by_cat.itertuples():
        pct = (r.amount / total * 100) if total else 0
        bar = (r.amount / max_amt * 100) if max_amt else 0
        color = colors.get(r.category, "#DA7756")
        rows.append(
            f'<div class="ledger-row">'
            f'<span class="swatch" style="background:{html.escape(color)}"></span>'
            f'<span class="cat-name">{html.escape(r.category)}</span>'
            f'<span class="leader"></span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{bar:.0f}%;background:{html.escape(color)}"></span></span>'
            f'<span class="cat-pct">{pct:.0f}%</span>'
            f'<span class="cat-amount">{html.escape(_fmt(r.amount, symbol))}</span>'
            f"</div>"
        )
    return "\n".join(rows)


def _stat_value(key: str, stats: dict[str, str], symbol: str) -> str:
    val = stats.get(key, "—")
    if val == "—":
        return val
    if key in {
        "avg_daily_spending",
        "highest_transaction",
        "lowest_transaction",
        "avg_transaction",
        "top_category_amount",
    }:
        try:
            return _fmt(float(str(val).replace(",", "")), symbol)
        except ValueError:
            return html.escape(str(val))
    if key == "highest_merchant" and stats.get("highest_transaction"):
        try:
            amt = _fmt(float(stats["highest_transaction"].replace(",", "")), symbol)
            return f"{html.escape(str(val))} ({amt})"
        except ValueError:
            pass
    if key == "top_category" and stats.get("top_category_amount"):
        try:
            amt = _fmt(float(stats["top_category_amount"].replace(",", "")), symbol)
            return f"{html.escape(str(val))} ({amt})"
        except ValueError:
            pass
    return html.escape(str(val))


def _stats_grid(stats: dict[str, str], symbol: str) -> str:
    tiles = []
    for key in _DISPLAY_STATS:
        label = STAT_LABELS.get(key, key.replace("_", " ").title())
        tiles.append(
            f'<div class="stat-tile">'
            f'<span class="stat-label">{html.escape(label)}</span>'
            f'<span class="stat-value">{_stat_value(key, stats, symbol)}</span>'
            f"</div>"
        )
    return "\n".join(tiles)


def _tx_rows(debits: pd.DataFrame, symbol: str) -> str:
    rows = []
    for r in debits.sort_values("post_date", ascending=False).itertuples():
        merchant = r.description
        if r.location:
            merchant = f"{r.description} — {r.location}"
        rows.append(
            f'<tr data-category="{html.escape(r.category)}">'
            f'<td class="date">{html.escape(r.post_date)}</td>'
            f'<td class="merchant">{html.escape(merchant)}</td>'
            f'<td class="tag"><span class="pill">{html.escape(r.category)}</span></td>'
            f'<td class="amount">{html.escape(_fmt(r.amount, symbol))}</td>'
            f"</tr>"
        )
    return "".join(rows) or '<tr><td colspan="4">No transactions</td></tr>'


def _filter_buttons(categories: list[str]) -> str:
    buttons = ['<button type="button" data-filter="all" class="active">All</button>']
    buttons.extend(
        f'<button type="button" data-filter="{html.escape(c)}">{html.escape(c)}</button>'
        for c in sorted(categories)
    )
    return "\n".join(buttons)


def _meta_float(meta: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        if key not in meta:
            continue
        try:
            return float(str(meta[key]).replace(",", ""))
        except ValueError:
            continue
    return None


def _fmt_meta(meta: dict[str, str], key: str, symbol: str) -> str:
    val = _meta_float(meta, key)
    return _fmt(val, symbol) if val is not None else "—"


def build_html(
    df: pd.DataFrame,
    meta: dict[str, str],
    stats: dict[str, str],
    source_key: str,
    cfg: Config,
) -> str:
    debits = df[df["kind"] == "debit"].copy()
    credits = df[df["kind"] == "credit"].copy()
    by_cat = (
        debits.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    total_spend = float(debits["amount"].sum()) if not debits.empty else 0.0
    total_credit = float(credits["amount"].sum()) if not credits.empty else 0.0
    sym = cfg.currency_symbol

    period_line = "—"
    if meta.get("period_start") and meta.get("period_end"):
        period_line = f"{meta['period_start']} – {meta['period_end']}"

    generated = datetime.now(timezone.utc).strftime("%d %b %Y")
    statement_total = _meta_float(meta, "total_account_balance", "total_due")
    if statement_total is not None:
        hero_label = "Total Due"
        whole, cents = _money_parts(statement_total, sym)
    else:
        hero_label = "Total Spent"
        whole, cents = _money_parts(total_spend, sym)

    categories = sorted(debits["category"].unique()) if not debits.empty else []
    colors = _category_colors(cfg, categories)

    title = cfg.report_title
    if meta.get("period_end"):
        title = f"{cfg.report_title} — {meta['period_end']}"

    total_due = meta.get("total_due", "—")
    acct_bal = meta.get("total_account_balance", "—")
    sub_parts = []
    if acct_bal != "—" and acct_bal != total_due:
        sub_parts.append(f"Account balance {sym}{acct_bal}")
    if meta.get("purchases_debits"):
        sub_parts.append(f"Purchases {sym}{meta['purchases_debits']}")
    if meta.get("payments_credits"):
        sub_parts.append(f"Payments {sym}{meta['payments_credits']}")
    elif total_credit:
        sub_parts.append(f"Credits {sym}{total_credit:,.2f}")
    sub_line = (
        " · ".join(sub_parts) if sub_parts else f"Parsed spend {sym}{total_spend:,.2f}"
    )

    min_payment = _fmt_meta(meta, "minimum_payment", sym)
    purchases = _fmt_meta(meta, "purchases_debits", sym)
    if purchases == "—" and total_spend:
        purchases = _fmt(total_spend, sym)

    insight = stats.get("insight_note", "").strip()
    insight_html = (
        f'<p class="insight-note">{html.escape(insight)}</p>' if insight else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,600&display=swap" rel="stylesheet">
<style>{_CSS}</style>
</head>
<body>
<div class="report">
  <header class="masthead">
    <div>
      <div class="eyebrow">{html.escape(cfg.report_eyebrow)}</div>
      <h1>{html.escape(cfg.report_title)}</h1>
    </div>
    <div class="period">
      {html.escape(period_line)}<br>
      Generated {html.escape(generated)}
    </div>
  </header>

  <section class="hero">
    <div class="hero-total">
      <div class="label">{html.escape(hero_label)}</div>
      <div class="amount">{html.escape(whole)}<span class="cents">{html.escape(cents)}</span></div>
      <div class="sub">{html.escape(sub_line)}</div>
    </div>
    <div class="hero-stats">
      <div class="stat-card">
        <span class="stat-label">Minimum payment</span>
        <span class="stat-value">{html.escape(min_payment)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Purchases & debits</span>
        <span class="stat-value">{html.escape(purchases)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Transactions</span>
        <span class="stat-value">{len(debits)}</span>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="section-head">
      <span class="num">01</span>
      <h2>Spending by Category</h2>
      <span class="rule"></span>
    </div>
    <div class="ledger">
      {_ledger_rows(by_cat, total_spend, colors, sym)}
    </div>
  </section>

  <section class="section">
    <div class="section-head">
      <span class="num">02</span>
      <h2>Key Statistics</h2>
      <span class="rule"></span>
    </div>
    <div class="stats-grid">
      {_stats_grid(stats, sym)}
    </div>
    {insight_html}
  </section>

  <section class="section">
    <div class="section-head">
      <span class="num">03</span>
      <h2>Transactions</h2>
      <span class="rule"></span>
    </div>
    <div class="filters">
      {_filter_buttons(categories)}
    </div>
    <table class="transactions" id="tx-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Merchant</th>
          <th>Category</th>
          <th class="num">Amount</th>
        </tr>
      </thead>
      <tbody>
        {_tx_rows(debits, sym)}
      </tbody>
    </table>
  </section>

  <footer class="footnote">
    <span>{len(debits)} transactions across {len(categories)} categories · source {html.escape(source_key)}</span>
    <span>Amounts in {html.escape(cfg.currency_code)}.</span>
  </footer>
</div>
<script>
document.querySelectorAll(".filters button").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll(".filters button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const cat = btn.dataset.filter;
    document.querySelectorAll("#tx-table tbody tr").forEach(row => {{
      row.classList.toggle("hidden", cat !== "all" && row.dataset.category !== cat);
    }});
  }});
}});
</script>
</body>
</html>"""
