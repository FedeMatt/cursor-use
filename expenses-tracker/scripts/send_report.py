"""Email the current-month HTML expense report (stdlib SMTP)."""

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import _bootstrap  # noqa: F401
from config import load_config
from generate_report import _report_key
from r2_util import bucket_name, list_objects, load_dotenv, r2_client, read_object_bytes


def _smtp_config() -> tuple[str, int, str, str] | None:
    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not host or not user or not password:
        return None
    port = int(os.environ.get("SMTP_PORT", "587"))
    return host, port, user, password


def send_report(*, dry_run: bool = False) -> str | None:
    to_addr = os.environ.get("REPORT_EMAIL_TO", "").strip()
    if not to_addr:
        print("email skipped (REPORT_EMAIL_TO not set)")
        return None

    smtp = _smtp_config()
    if not smtp:
        raise SystemExit("SMTP_HOST, SMTP_USER, and SMTP_PASSWORD are required")

    cfg = load_config()
    client = r2_client()
    bucket = bucket_name()
    report_key = _report_key(cfg)
    if not any(
        k == report_key for k, _ in list_objects(client, bucket, cfg.reports_prefix)
    ):
        raise SystemExit(f"report not found in R2: {report_key}")

    html = read_object_bytes(client, bucket, report_key).decode()
    when = datetime.now(timezone.utc)
    subject = os.environ.get("REPORT_EMAIL_SUBJECT") or (
        f"{cfg.report_title} — {when:%B %Y}"
    )
    from_addr = os.environ.get("REPORT_EMAIL_FROM") or smtp[2]

    if dry_run:
        print(f"would email {to_addr}: {subject} ({len(html)} bytes)")
        return report_key

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(html, "html", "utf-8"))

    host, port, user, password = smtp
    with smtplib.SMTP(host, port, timeout=60) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"emailed {report_key} → {to_addr}")
    return report_key


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        send_report(dry_run=args.dry_run)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
