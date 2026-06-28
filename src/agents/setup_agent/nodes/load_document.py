# load_document.py

import os
from src.agents.setup_agent.schema.global_state import AgentState


def load_document(state: AgentState) -> AgentState:
    """
    Validate uploaded file and detect document type.
    """

    print("[load_document] START", {k: state.get(k) for k in ("file_path", "template_id")})

    file_path = state["file_path"]

    # Check file exists in temp storage
    if not os.path.exists(file_path):
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
        return {
            **state,
            "error": f"Unsupported file type: {extension}"
        }

    result = {
        "file_type": file_type,
        "error": None,
    }
    print("[load_document] END", result)
    return result