# nodes/extract_docx_blueprint.py

import json
from pathlib import Path

from src.core.config import settings 
from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.helpers.docx.docx_parser import parse_docx

from src.agents.setup_agent.utils.template_storage import save_template


def extract_docx_blueprint(state: AgentState) -> AgentState:
    """
    Extract DOCX blueprint and store it.
    """

    try:
        print("[extract_docx_blueprint] START", {k: state.get(k) for k in ("file_path", "template_id")})

        file_path = state["file_path"]
        template_id = state["template_id"]

        # Extract blueprint from DOCX
        blueprint = parse_docx(file_path)

        # Always save to Firestore / local mock Firestore database
        save_template(
            template_id=template_id,
            lawyer_id=state["lawyer_id"],
            blueprint=blueprint,
        )

        result = {
            "docx_blueprint": [blueprint],
            "error": None,
        }
        print("[extract_docx_blueprint] END", {"template_id": template_id})
        return result

    except Exception as e:
        print("[extract_docx_blueprint] ERROR", str(e))
        return {"extract_docx_blueprint_error": str(e)}