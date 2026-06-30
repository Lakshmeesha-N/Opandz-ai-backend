# src/agents/case_intake_agent/helpers/evidence/extract_file_content.py

import logging
import tempfile
from pathlib import Path

from src.agents.case_intake_agent.helpers.extract_pdf_text import (
    extract_pdf_text,
)

from src.agents.case_intake_agent.helpers.extract_docx_text import (
    extract_docx_text,
)

from src.agents.case_intake_agent.helpers.extract_image_text import (
    extract_image_text,
)

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_TYPES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def _download_from_gcs(gcs_uri: str) -> str:
    """Download a file from GCS to a local temp file. Returns the local path."""
    from src.core import firebase
    firebase.ensure_globals()
    bucket = firebase.bucket
    if bucket is None:
        raise RuntimeError("Firebase Storage bucket is not initialized.")

    without_scheme = gcs_uri[len("gs://"):]
    bucket_name, _, blob_path = without_scheme.partition("/")

    from google.cloud import storage as gcs
    client = gcs.Client()
    gcs_bucket = client.bucket(bucket_name)
    blob = gcs_bucket.blob(blob_path)

    suffix = Path(blob_path).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    blob.download_to_filename(tmp.name)
    logger.info("[extract_file_content] Downloaded GCS file %s → %s", gcs_uri, tmp.name)
    return tmp.name


async def extract_file_content(
    file_path: str,
) -> dict:
    """
    Extract content from a supported file.
    Supports both local paths and GCS URIs (gs://...).

    Returns:
    {
        "file_name": "...",
        "file_type": "...",
        "content": "..."
    }
    """
    
    local_path = file_path
    if file_path.startswith("gs://"):
        try:
            local_path = _download_from_gcs(file_path)
        except Exception as e:
            logger.exception("[extract_file_content] Failed to download from GCS: %s", file_path)
            raise RuntimeError(f"Failed to download file from storage: {e}")

    path = Path(local_path)

    if not path.exists():
        logger.error("[extract_file_content] File not found: %s", file_path)
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()
    logger.info("[extract_file_content] Extracting content from: %s (ext: %s)", path.name, extension)

    try:
        # PDF
        if extension == ".pdf":
            content = await extract_pdf_text(
                local_path
            )
            file_type = "pdf"

        # DOCX
        elif extension == ".docx":
            content = await extract_docx_text(
                local_path
            )
            file_type = "docx"

        # Images
        elif extension in SUPPORTED_IMAGE_TYPES:
            content = await extract_image_text(
                local_path
            )
            file_type = "image"

        else:
            logger.error("[extract_file_content] Unsupported file type: %s", extension)
            raise ValueError(
                f"Unsupported file type: {extension}"
            )
    finally:
        # If we downloaded a temp copy from GCS, clean it up after extraction
        if file_path.startswith("gs://") and local_path != file_path:
            try:
                import os
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info("[extract_file_content] Cleaned up downloaded temp file: %s", local_path)
            except Exception as e:
                logger.exception("Failed to cleanup downloaded file %s", local_path)

    logger.info("[extract_file_content] Successfully extracted content from: %s", path.name)
    return {
        "file_name": path.name,
        "file_type": file_type,
        "content": content,
    }