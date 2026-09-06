import logging
import os
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile
import vercel_blob
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback local storage directory
root = Path(settings.STORAGE_DIR)
try:
    root.mkdir(parents=True, exist_ok=True)
except OSError:
    pass


def is_blob_url(storage_key: str) -> bool:
    """
    Check if the storage key represents a remote Vercel Blob URL.
    """
    if not storage_key:
        return False
    return (
        storage_key.startswith("http://")
        or storage_key.startswith("https://")
        or "blob.vercel-storage.com" in storage_key
    )


async def save_upload(upload: UploadFile) -> Tuple[str, int]:
    """
    Save an uploaded file to Vercel Blob Storage if configured,
    or fall back to local disk storage for local development.

    Returns:
        tuple (storage_key, file_size)
    """
    filename = Path(upload.filename or "file").name
    key = f"{uuid.uuid4().hex}_{filename}"

    content = await upload.read()
    size = len(content)

    blob_token = settings.BLOB_READ_WRITE_TOKEN or os.environ.get("BLOB_READ_WRITE_TOKEN")

    if blob_token:
        try:
            logger.info("Uploading %s to Vercel Blob Object Storage...", key)
            # Use multipart for large files (> 10MB)
            use_multipart = size > 10 * 1024 * 1024
            resp = vercel_blob.put(
                path=key,
                data=content,
                options={
                    "token": blob_token,
                    "addRandomSuffix": "false",
                    "allowOverwrite": "true",
                },
                multipart=use_multipart,
            )

            blob_url = resp.get("url")
            if not blob_url:
                raise RuntimeError(f"Vercel Blob did not return a valid URL: {resp}")

            logger.info("Successfully uploaded %s to Vercel Blob: %s", key, blob_url)
            return blob_url, size

        except Exception as e:
            logger.error("Failed to upload to Vercel Blob: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to upload file to Vercel Blob storage: {str(e)}") from e

    # Fallback to local storage (e.g. offline dev without credentials)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    dest = root / key
    dest.write_bytes(content)
    return key, size


def get_file_target(storage_key: str) -> Tuple[str, bool]:
    """
    Determine download target for a given storage key.

    Returns:
        (target_path_or_url, is_remote_url)
    """
    if is_blob_url(storage_key):
        return storage_key, True

    local_path = root / storage_key
    return str(local_path), False


def path(storage_key: str) -> Path:
    """
    Backwards-compatible helper returning local Path.
    """
    return root / storage_key


def remove(storage_key: str) -> None:
    """
    Delete a file from Vercel Blob Storage or local disk.
    """
    if not storage_key:
        return

    if is_blob_url(storage_key):
        blob_token = settings.BLOB_READ_WRITE_TOKEN or os.environ.get("BLOB_READ_WRITE_TOKEN")
        if blob_token:
            try:
                vercel_blob.delete(
                    storage_key,
                    options={"token": blob_token},
                )
                logger.info("Deleted blob from Vercel Blob storage: %s", storage_key)
            except Exception as e:
                logger.warning("Failed to delete blob from Vercel Blob storage: %s", e)
    else:
        try:
            p = root / storage_key
            if p.exists():
                p.unlink()
        except OSError as e:
            logger.warning("Failed to delete local file %s: %s", storage_key, e)
