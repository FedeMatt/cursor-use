"""Shared R2 / env helpers for expenses-tracker."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env(primary: str, fallback: str) -> str:
    return os.environ.get(primary) or os.environ[fallback]


def r2_client():
    account_id = env("R2_ACCOUNT_ID", "ACCOUNT_ID")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=env("R2_ACCESS_KEY_ID", "ACCESS_KEY_ID"),
        aws_secret_access_key=env("R2_SECRET_ACCESS_KEY", "SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def bucket_name() -> str:
    return env("R2_BUCKET", "BUCKET_NAME")


def is_current_month(when: datetime) -> bool:
    now = datetime.now(timezone.utc)
    when = when.astimezone(timezone.utc)
    return when.year == now.year and when.month == now.month


def list_objects(client, bucket: str, prefix: str) -> list[tuple[str, datetime]]:
    objects: list[tuple[str, datetime]] = []
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            objects.append((key, obj["LastModified"]))
    return objects


def read_object(client, bucket: str, key: str) -> str:
    return client.get_object(Bucket=bucket, Key=key)["Body"].read().decode()


def write_object(client, bucket: str, key: str, body: str, content_type: str) -> None:
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode(),
        ContentType=content_type,
    )
