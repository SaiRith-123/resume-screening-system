"""File validation + safe storage helpers (spec §4, §22)."""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from dataclasses import dataclass

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",  # some browsers send this for docx
}
_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]")


class FileValidationError(ValueError):
    pass


@dataclass
class ValidatedFile:
    safe_name: str
    stored_path: str
    content_type: str
    size_bytes: int
    sha256: str


def sanitize_filename(filename: str) -> str:
    """Prevent path traversal / weird characters (spec §22 safe file names)."""
    base = os.path.basename(filename or "resume").strip()
    base = _SAFE_RE.sub("_", base)
    base = base.lstrip(".") or "resume"
    return base[:120]


def validate_upload(filename: str, content_type: str | None, size_bytes: int) -> None:
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"unsupported_file_type:{ext or 'none'}")
    if content_type and content_type not in ALLOWED_MIME and "pdf" not in content_type and "word" not in content_type:
        raise FileValidationError(f"unsupported_mime_type:{content_type}")
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if size_bytes <= 0:
        raise FileValidationError("empty_file")
    if size_bytes > max_bytes:
        raise FileValidationError(f"file_too_large:{size_bytes}>{max_bytes}")


def store_upload(filename: str, content: bytes, content_type: str | None,
                 job_id: int) -> ValidatedFile:
    validate_upload(filename, content_type, len(content))
    safe = sanitize_filename(filename)
    stored_name = f"{uuid.uuid4().hex}_{safe}"
    if settings.STORAGE_BACKEND.lower() == "s3":
        if not settings.S3_BUCKET:
            raise FileValidationError("remote_storage_not_configured")
        import boto3

        client = boto3.client(
            "s3", region_name=settings.S3_REGION or None,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
        )
        key = f"jobs/{job_id}/resumes/{stored_name}"
        client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=content,
                          ContentType=content_type or "application/octet-stream")
        stored_path = f"s3://{settings.S3_BUCKET}/{key}"
    else:
        target_dir = os.path.join(settings.UPLOAD_DIR, f"job_{job_id}")
        os.makedirs(target_dir, exist_ok=True)
        stored_path = os.path.join(target_dir, stored_name)
        with open(stored_path, "wb") as fh:
            fh.write(content)
    digest = hashlib.sha256(content).hexdigest()
    return ValidatedFile(
        safe_name=safe, stored_path=stored_path,
        content_type=content_type or "application/octet-stream",
        size_bytes=len(content), sha256=digest,
    )


def read_stored_file(stored_path: str) -> bytes:
    """Read an object for processing/download without exposing storage credentials."""
    if stored_path.startswith("s3://"):
        import boto3

        bucket, key = stored_path[5:].split("/", 1)
        client = boto3.client(
            "s3", region_name=settings.S3_REGION or None,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
        )
        return client.get_object(Bucket=bucket, Key=key)["Body"].read()
    with open(stored_path, "rb") as handle:
        return handle.read()
