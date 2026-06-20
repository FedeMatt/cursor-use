"""Build an HTML expense report from current-month statement markdown in R2."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import _bootstrap  # noqa: F401
from config import Config, load_config
from r2_util import (
    bucket_name,
    is_current_month,
    list_objects,
    load_dotenv,
    r2_client,
    read_object,
    write_object,
)
from report_html import build_html
from statement_parse import parse_meta
from statistics import resolve_statistics
from transactions import parse_transactions


def _current_md_key(client, bucket: str, cfg: Config) -> str | None:
    objs = [
        (key, modified)
        for key, modified in list_objects(client, bucket, cfg.markdown_prefix)
        if key.lower().endswith(".md") and is_current_month(modified)
    ]
    if not objs:
        return None
    cleaned = [(k, m) for k, m in objs if k.lower().endswith(".cleaned.md")]
    if cleaned:
        return max(cleaned, key=lambda x: x[1])[0]
    raw = [(k, m) for k, m in objs if not k.lower().endswith(".cleaned.md")]
    if raw:
        return max(raw, key=lambda x: x[1])[0]
    return None


def _report_key(cfg: Config) -> str:
    when = datetime.now(timezone.utc)
    return f"{cfg.reports_prefix.rstrip('/')}/{when:%Y-%m}.html"


def generate_report(
    cfg: Config | None = None, *, dry_run: bool = False, force: bool = False
) -> str | None:
    cfg = cfg or load_config()
    client = r2_client()
    bucket = bucket_name()
    md_key = _current_md_key(client, bucket, cfg)
    if not md_key:
        return None

    report_key = _report_key(cfg)
    if not force and any(
        k == report_key for k, _ in list_objects(client, bucket, cfg.reports_prefix)
    ):
        return report_key

    md = read_object(client, bucket, md_key)
    df = parse_transactions(md, cfg)
    meta = parse_meta(md, cfg)
    stats = resolve_statistics(md, df, meta, cfg)
    html_doc = build_html(df, meta, stats, md_key, cfg)

    if dry_run:
        print(f"would write {report_key} ({len(df)} rows)")
        return report_key

    write_object(client, bucket, report_key, html_doc, "text/html; charset=utf-8")
    return report_key


def _self_check() -> None:
    cfg = load_config()
    sample = """
|23 May|21May|DBS BANK MATTEO||3,100.00CR|
|22 May|22May|Grab*A-9CCDSA2GWDUS5AV||22.40|
|30 May|28 May|NTUC FairPrice Online SINGAPORE||137.31|
|03 Jun|02 Jun|Spotify P4315EA5D9|Stockholm|20.98|
"""
    df = parse_transactions(sample, cfg)
    assert len(df) == 4
    meta = {"total_due": "100.00", "period_end": "18 JUN 2026"}
    stats = resolve_statistics("", df, meta, cfg)
    html_doc = build_html(df, meta, stats, "sample.md", cfg)
    assert cfg.report_title in html_doc
    assert "Key Statistics" in html_doc
    assert "stats-grid" in html_doc


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, help="Path to config.toml")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config) if args.config else load_config()

    if args.self_check:
        _self_check()
        print("self-check ok")
    else:
        key = generate_report(cfg, dry_run=args.dry_run, force=args.force)
        if key:
            print(key)
        else:
            print("no current-month markdown found")
            sys.exit(1)
