# src/agents/document_generation_agent/helpers/storage_fallback.py

import logging
from src.core import firebase

logger = logging.getLogger(__name__)


def upload_code_to_storage(
    template_id: str,
    document_id: str,
    code: str,
) -> str:
    """
    Upload generated DOCX.js code to Firebase Storage.
    Returns the gs:// URI of the uploaded file.
    """
    firebase.ensure_globals()
    bucket = firebase.bucket
    gcs_path = f"templates/{template_id}/{document_id}.js"
    
    if bucket is None:
        # Fallback to local file mock in test/dev
        from pathlib import Path
        local_path = Path("temp") / "storage_fallback" / gcs_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(code, encoding="utf-8")
        gcs_uri = f"gs://local-mock/{gcs_path}"
        logger.warning("[storage_fallback] GCS not available. Saved locally to mock URI: %s", gcs_uri)
        return gcs_uri

    blob = bucket.blob(gcs_path)
    blob.upload_from_string(
        code,
        content_type="application/javascript",
    )
    
    gcs_uri = f"gs://{bucket.name}/{gcs_path}"
    logger.info("[storage_fallback] Successfully uploaded code to GCS: %s", gcs_uri)
    return gcs_uri


def read_code_from_storage(gcs_uri: str) -> str:
    """
    Download code from GCS and return it as a string.
    """
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")

    without_scheme = gcs_uri[len("gs://"):]
    bucket_name, _, blob_path = without_scheme.partition("/")

    if bucket_name == "local-mock":
        from pathlib import Path
        local_path = Path("temp") / "storage_fallback" / blob_path
        if local_path.exists():
            code = local_path.read_text(encoding="utf-8")
            logger.info("[storage_fallback] Read code from local GCS mock: %s", local_path)
            return code
        raise FileNotFoundError(f"Local mock GCS file not found: {local_path}")

    firebase.ensure_globals()
    bucket = firebase.bucket
    if bucket is None:
        raise RuntimeError("Firebase Storage bucket is not initialized.")

    # Get blob from the correct bucket
    from google.cloud import storage as gcs
    client = gcs.Client()
    gcs_bucket = client.bucket(bucket_name)
    blob = gcs_bucket.blob(blob_path)

    code = blob.download_as_text()
    logger.info("[storage_fallback] Successfully read code from GCS URI: %s", gcs_uri)
    return code

