# load_document.py

import os
import logging
from src.agents.setup_agent.schema.global_state import AgentState

logger = logging.getLogger(__name__)


def load_document(state: AgentState) -> AgentState:
    """
    Validate uploaded file and detect document type.
    """

    logger.info("[load_document] START: file_path=%s, template_id=%s", state.get("file_path"), state.get("template_id"))

    file_path = state["file_path"]

    # Check file exists in temp storage
    if not os.path.exists(file_path):
        logger.error("[load_document] Uploaded file not found at: %s", file_path)
        return {
            **state,
            "error": "Uploaded file not found"
        }

    # Detect extension
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".docx":
        file_type = "docx"

    elif extension == ".pdf":
        file_type = "pdf"

    else:
        logger.error("[load_document] Unsupported file type: %s", extension)
        return {
            **state,
            "error": f"Unsupported file type: {extension}"
        }

    result = {
        "file_type": file_type,
        "error": None,
    }
    logger.info("[load_document] END: file_type=%s", file_type)
    return result