# load_document.py

import os
import logging
import tempfile
from src.agents.setup_agent.schema.global_state import AgentState

logger = logging.getLogger(__name__)


def _download_from_gcs(gcs_uri: str) -> str:
    """Download a file from GCS to a local temp file. Returns the local path."""
    from src.core import firebase
    firebase.ensure_globals()
    bucket = firebase.bucket
    if bucket is None:
        raise RuntimeError("Firebase Storage bucket is not initialized.")

    # Parse gs://bucket-name/path/to/file
    without_scheme = gcs_uri[len("gs://"):]
    bucket_name, _, blob_path = without_scheme.partition("/")

    # Get blob from the correct bucket
    from google.cloud import storage as gcs
    client = gcs.Client()
    gcs_bucket = client.bucket(bucket_name)
    blob = gcs_bucket.blob(blob_path)

    # Download to a temp file preserving the extension
    suffix = os.path.splitext(blob_path)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    blob.download_to_filename(tmp.name)
    logger.info("[load_document] Downloaded GCS file %s → %s", gcs_uri, tmp.name)
    return tmp.name


def load_document(state: AgentState) -> AgentState:
    """
    Validate uploaded file and detect document type.
    Supports both local paths and GCS URIs (gs://...).
    """

    logger.info("[load_document] START: file_path=%s, template_id=%s", state.get("file_path"), state.get("template_id"))

    file_path = state["file_path"]
    local_path = file_path

    # If file is on GCS, download it first
    if file_path and file_path.startswith("gs://"):
        try:
            local_path = _download_from_gcs(file_path)
        except Exception as e:
            logger.exception("[load_document] Failed to download from GCS: %s", file_path)
            return {**state, "error": f"Failed to download file from storage: {e}"}

    # Check file exists
    if not os.path.exists(local_path):
        logger.error("[load_document] File not found at: %s", local_path)
        return {**state, "error": "Uploaded file not found"}

    # Detect extension
    extension = os.path.splitext(local_path)[1].lower()

    if extension == ".docx":
        file_type = "docx"
    elif extension == ".pdf":
        file_type = "pdf"
    else:
        logger.error("[load_document] Unsupported file type: %s", extension)
        return {**state, "error": f"Unsupported file type: {extension}"}

    result = {
        "file_path": local_path,  # Update state to use the local path for downstream nodes
        "file_type": file_type,
        "error": None,
    }
    logger.info("[load_document] END: file_type=%s, local_path=%s", file_type, local_path)
    return result