"""Convert credit-card PDF bills in R2 to markdown under monthly-expense/."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import PurePosixPath

import _bootstrap  # noqa: F401
import pymupdf4llm
from config import load_config
from r2_util import (
    bucket_name,
    is_current_month,
    list_objects,
    load_dotenv,
    r2_client,
    write_object,
)

OCR_LANGUAGE = os.environ.get("R2_OCR_LANGUAGE", "eng")


def _ensure_tesseract() -> None:
    if shutil.which("tesseract"):
        return
    raise SystemExit(
        "tesseract not found — install it for OCR (e.g. brew install tesseract "
        "or apt-get install tesseract-ocr)"
    )


def _pdf_to_markdown(pdf_bytes: bytes, *, ocr: bool = True) -> str:
    if ocr:
        _ensure_tesseract()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        kwargs = (
            {"use_ocr": True, "force_ocr": True, "ocr_language": OCR_LANGUAGE}
            if ocr
            else {}
        )
        return pymupdf4llm.to_markdown(tmp.name, **kwargs)


def _dest_key(source_key: str, dest_prefix: str) -> str:
    name = PurePosixPath(source_key).stem + ".md"
    return f"{dest_prefix.rstrip('/')}/{name}"


def process_bills(*, dry_run: bool = False, force: bool = False) -> list[str]:
    cfg = load_config()
    bucket = bucket_name()
    client = r2_client()
    existing = (
        set()
        if force
        else {
            PurePosixPath(key).stem
            for key, _ in list_objects(client, bucket, cfg.markdown_prefix)
            if not key.endswith(".cleaned.md")
        }
    )
    written: list[str] = []

    for key, modified in sorted(list_objects(client, bucket, cfg.source_prefix)):
        if not key.lower().endswith(".pdf"):
            continue
        if not is_current_month(modified):
            continue
        if PurePosixPath(key).stem in existing:
            continue
        dest = _dest_key(key, cfg.markdown_prefix)
        if dry_run:
            written.append(dest)
            continue
        pdf = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        md = _pdf_to_markdown(pdf)
        write_object(
            client,
            bucket,
            dest,
            md,
            "text/markdown; charset=utf-8",
        )
        written.append(dest)
    return written


def _self_check() -> None:
    sample = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 200 50]/Parent 2 0 R/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 10 30 Td (hello bill) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
0000000178 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
272
%%EOF"""
    md = _pdf_to_markdown(sample, ocr=False)
    assert "hello" in md.lower(), md

    now = datetime.now(timezone.utc)
    assert is_current_month(now)
    assert not is_current_month(now.replace(month=now.month % 12 + 1))


if __name__ == "__main__":
    load_dotenv()
    args = set(sys.argv[1:])
    if "--self-check" in args:
        _self_check()
        print("self-check ok")
    else:
        results = process_bills(
            dry_run="--dry-run" in args,
            force="--force" in args,
        )
        if results:
            print("\n".join(results))
        else:
            print("nothing to process")
