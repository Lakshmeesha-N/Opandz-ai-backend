# nodes/extract_docx_blueprint.py

import json
import logging
from pathlib import Path

from src.core.config import settings 
from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.helpers.docx.docx_parser import parse_docx

from src.agents.setup_agent.utils.template_storage import save_template

logger = logging.getLogger(__name__)


def extract_docx_blueprint(state: AgentState) -> AgentState:
    """
    Extract DOCX blueprint and store it.
    """

    try:
        logger.info("[extract_docx_blueprint] START: file_path=%s, template_id=%s", state.get("file_path"), state.get("template_id"))

        file_path = state["file_path"]
        template_id = state["template_id"]

        # Extract blueprint from DOCX
        blueprint = parse_docx(file_path)

        result = {
            "docx_blueprint": [blueprint],
            "error": None,
        }
        logger.info("[extract_docx_blueprint] END: template_id=%s", template_id)
        return result

    except Exception as e:
        logger.exception("[extract_docx_blueprint] ERROR: %s", str(e))
        return {"extract_docx_blueprint_error": str(e)}