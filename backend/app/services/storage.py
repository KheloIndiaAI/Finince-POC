"""S3 storage for the uploaded originals. One prefix per comparison.

The boto3 client is built lazily so importing this module (in tests, or on a
machine without AWS credentials) never touches the network.
"""
from __future__ import annotations

import uuid
from pathlib import PurePosixPath

import boto3

from app.config import settings

_client = None


def client():
    """Return the shared S3 client, creating it on first use."""
    global _client
    if _client is None:
        _client = boto3.client("s3", region_name=settings.aws_region)
    return _client


def build_key(comparison_id: uuid.UUID, document_type: str, file_name: str) -> str:
    """S3 key: comparisons/<id>/<sanction|uc>/<file name>."""
    safe_name = PurePosixPath(file_name.replace("\\", "/")).name or "upload"
    return f"comparisons/{comparison_id}/{document_type.lower()}/{safe_name}"


def upload_bytes(key: str, data: bytes, content_type: str) -> str:
    """Store the bytes at `key` in the configured bucket; return the key."""
    client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def presigned_url(key: str, expires_in: int = 3600) -> str:
    """A short-lived URL so the frontend can open/download a private object."""
    return client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def delete_object(key: str) -> None:
    """Best-effort delete; a missing key/object is not an error."""
    client().delete_object(Bucket=settings.s3_bucket, Key=key)
