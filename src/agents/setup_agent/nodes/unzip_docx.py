# nodes/unzip_docx.py

import logging
import os
import shutil
import tempfile
import zipfile

from src.agents.setup_agent.schema.global_state import AgentState

logger = logging.getLogger(__name__)


def unzip_docx(state: AgentState) -> AgentState:
    """
    Unzip the .docx file into a local temp directory.

    DOCX files are ZIP archives containing XML files (word/document.xml,
    word/styles.xml, word/numbering.xml, word/theme/theme1.xml, etc.).
    This node extracts them into ./temp/<template_id>/ so downstream
    nodes can read the raw XML when needed.
    """

    try:
        file_path = state["file_path"]
        template_id = state["template_id"]

        logger.info(
            "[unzip_docx] START: file_path=%s, template_id=%s",
            file_path,
            template_id,
        )

        # Create temp directory: ./temp/<template_id>/
        temp_base = os.path.join(tempfile.gettempdir(), "opandz_temp")
        temp_dir = os.path.join(temp_base, template_id)

        # Clean any pre-existing temp for this template_id
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        os.makedirs(temp_dir, exist_ok=True)

        # Unzip the docx
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        logger.info(
            "[unzip_docx] END: extracted to %s", temp_dir
        )

        return {
            "temp_dir": temp_dir,
            "error": None,
        }

    except Exception as e:
        logger.exception("[unzip_docx] ERROR: %s", str(e))
        return {"error": f"unzip_docx failed: {str(e)}"}
