"""
Supabase Storage Helper
========================
Thin abstraction over the Supabase Storage API for uploading, downloading,
listing, and deleting report/metadata files in the ``reports`` bucket.

All storage paths mirror the previous local folder structure:
    model_training/recommendation_v1.3_training_report.json
    training_logs.json
    model_metadata.json

Why this module?
    Centralising all Supabase Storage calls here means:
    - A single place to swap storage backends in the future
    - Consistent error handling and logging across all callers
    - Easy to unit-test by mocking just this module

Graceful degradation:
    If Supabase is not configured (missing env vars), every function
    falls back silently and logs a warning.  The application continues
    to work using local disk only.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger("app.storage")

# Load env vars
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# The bucket name is configurable via .env
BUCKET_NAME = os.getenv("SUPABASE_STORAGE_BUCKET", "reports").strip("'\"")


def _get_client():
    """Return the Supabase client, or None if not configured."""
    try:
        from app.supabase_client import supabase  # type: ignore[import]
        return supabase
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Core Storage Operations
# ---------------------------------------------------------------------------

def upload_report(storage_path: str, content: bytes) -> bool:
    """
    Upload bytes to Supabase Storage.

    Parameters
    ----------
    storage_path : str
        Path inside the bucket, e.g. ``"model_training/report_v1.3.json"``.
    content : bytes
        Raw bytes to upload (JSON encoded, pickle, etc.).

    Returns
    -------
    bool
        True on success, False on failure or when Supabase is not configured.
    """
    client = _get_client()
    if client is None:
        logger.warning(f"[storage] Supabase not configured — skipping upload of '{storage_path}'")
        return False

    try:
        # Upsert: overwrite if already exists (e.g. training_logs.json)
        client.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": _guess_content_type(storage_path),
                "upsert": "true",
            },
        )
        logger.info(f"[storage] Uploaded '{storage_path}' to bucket '{BUCKET_NAME}'")
        return True
    except Exception as exc:
        logger.error(f"[storage] Upload failed for '{storage_path}': {exc}")
        return False


def download_report(storage_path: str) -> Optional[bytes]:
    """
    Download a file from Supabase Storage.

    Parameters
    ----------
    storage_path : str
        Path inside the bucket.

    Returns
    -------
    bytes or None
        Raw bytes on success, None on failure or when Supabase is not configured.
    """
    client = _get_client()
    if client is None:
        logger.warning(f"[storage] Supabase not configured — cannot download '{storage_path}'")
        return None

    try:
        data = client.storage.from_(BUCKET_NAME).download(storage_path)
        logger.info(f"[storage] Downloaded '{storage_path}' from bucket '{BUCKET_NAME}'")
        return data
    except Exception as exc:
        err_msg = str(exc)
        if "not_found" in err_msg or "NoSuchKey" in err_msg or "Object not found" in err_msg:
            logger.info(f"[storage] Remote file '{storage_path}' not found in bucket '{BUCKET_NAME}' — falling back")
        else:
            logger.warning(f"[storage] Download failed for '{storage_path}': {exc}")
        return None


def upload_json(storage_path: str, data: Any) -> bool:
    """
    Serialise ``data`` to JSON and upload to Supabase Storage.

    Parameters
    ----------
    storage_path : str
        Path inside the bucket (e.g. ``"training_logs.json"``).
    data : Any
        JSON-serialisable Python object.

    Returns
    -------
    bool
        True on success.
    """
    try:
        content = json.dumps(data, indent=2, default=str).encode("utf-8")
        return upload_report(storage_path, content)
    except Exception as exc:
        logger.error(f"[storage] JSON serialisation failed for '{storage_path}': {exc}")
        return False


def download_json(storage_path: str) -> Optional[Any]:
    """
    Download a JSON file from Supabase Storage and parse it.

    Returns
    -------
    Any or None
        Parsed Python object, or None if unavailable.
    """
    raw = download_report(storage_path)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        logger.error(f"[storage] JSON parse failed for '{storage_path}': {exc}")
        return None


def list_reports(prefix: str = "") -> List[Dict[str, Any]]:
    """
    List all files in the bucket under an optional path prefix.

    Parameters
    ----------
    prefix : str
        Folder prefix, e.g. ``"model_training"``. Leave empty to list root.

    Returns
    -------
    list[dict]
        Each item contains at least ``name`` (str) and ``metadata`` (dict).
        Returns an empty list on failure or when Supabase is not configured.
    """
    client = _get_client()
    if client is None:
        logger.warning(f"[storage] Supabase not configured — cannot list reports")
        return []

    try:
        files = client.storage.from_(BUCKET_NAME).list(prefix)
        logger.info(f"[storage] Listed {len(files)} files under prefix '{prefix}'")
        return files or []
    except Exception as exc:
        logger.error(f"[storage] List failed for prefix '{prefix}': {exc}")
        return []


def delete_report(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage.

    Parameters
    ----------
    storage_path : str
        Path inside the bucket.

    Returns
    -------
    bool
        True on success, False on failure.
    """
    client = _get_client()
    if client is None:
        return False

    try:
        client.storage.from_(BUCKET_NAME).remove([storage_path])
        logger.info(f"[storage] Deleted '{storage_path}' from bucket '{BUCKET_NAME}'")
        return True
    except Exception as exc:
        logger.error(f"[storage] Delete failed for '{storage_path}': {exc}")
        return False


def get_public_url(storage_path: str) -> Optional[str]:
    """
    Get the public URL for a file (only works for public buckets).

    Returns
    -------
    str or None
        Public URL string, or None if the bucket is private or Supabase
        is not configured.
    """
    client = _get_client()
    if client is None:
        return None

    try:
        result = client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        return result
    except Exception as exc:
        logger.warning(f"[storage] Could not get public URL for '{storage_path}': {exc}")
        return None


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _guess_content_type(path: str) -> str:
    """Infer MIME type from file extension."""
    ext = Path(path).suffix.lower()
    return {
        ".json": "application/json",
        ".csv":  "text/csv",
        ".pkl":  "application/octet-stream",
        ".txt":  "text/plain",
    }.get(ext, "application/octet-stream")
