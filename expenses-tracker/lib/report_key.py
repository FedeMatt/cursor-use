"""Report R2 key naming — shared by generate_report and send_report."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PurePosixPath

from config import Config
from r2_util import is_current_month, list_objects


def report_key(cfg: Config, when: datetime | None = None) -> str:
    when = when or datetime.now(timezone.utc)
    return f"{cfg.reports_prefix.rstrip('/')}/{when:%Y-%m}.html"


def latest_report_key(client, bucket: str, cfg: Config) -> str | None:
    """Newest .html under reports_prefix modified this month (what generate_report writes)."""
    htmls = [
        (key, modified)
        for key, modified in list_objects(client, bucket, cfg.reports_prefix)
        if key.lower().endswith(".html") and is_current_month(modified)
    ]
    if not htmls:
        return None
    return max(htmls, key=lambda x: x[1])[0]


def resolve_report_key(
    client,
    bucket: str,
    cfg: Config,
    *,
    explicit: str | None = None,
) -> str:
    if explicit:
        return explicit
    if latest := latest_report_key(client, bucket, cfg):
        return latest
    return report_key(cfg)


def subject_for_report(cfg: Config, report_key_path: str) -> str:
    stem = PurePosixPath(report_key_path).stem
    try:
        when = datetime.strptime(stem, "%Y-%m").replace(tzinfo=timezone.utc)
        month_label = when.strftime("%B %Y")
    except ValueError:
        month_label = datetime.now(timezone.utc).strftime("%B %Y")
    return f"{cfg.report_title} — {month_label}"


if __name__ == "__main__":
    assert report_key(type("C", (), {"reports_prefix": "monthly-reports/"})()).endswith(
        ".html"
    )
    assert (
        subject_for_report(
            type("C", (), {"report_title": "Monthly Expense Report"})(),
            "monthly-reports/2026-06.html",
        )
        == "Monthly Expense Report — June 2026"
    )
    print("report_key ok")
