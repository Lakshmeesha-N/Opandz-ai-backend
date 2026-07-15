# src/agents/setup_agent/nodes/convert_pdf.py
import logging
import os
from src.agents.setup_agent.schema.global_state import AgentState
from src.agents.setup_agent.helpers.pdf_converter import convert_pdf_to_docx

logger = logging.getLogger(__name__)

def convert_pdf_node(state: AgentState) -> AgentState:
    """
    If the file is a PDF, convert it to DOCX and update the file_path and file_type in the state.
    """
    logger.info("[convert_pdf] START")
    
    file_path = state.get("file_path")
    file_type = state.get("file_type")
    
    if not file_path or file_type != "pdf":
        logger.info("[convert_pdf] Skipping conversion because file is not a PDF")
        return state
        
    docx_path = file_path.rsplit(".", 1)[0] + ".docx"
    
    logger.info(f"[convert_pdf] Converting {file_path} to {docx_path}")
    
    success = convert_pdf_to_docx(file_path, docx_path)
    
    if not success:
        return {**state, "error": "Failed to convert PDF to DOCX."}
        
    result = {
        "file_path": docx_path,
        "file_type": "docx",
        "error": None
    }
    logger.info("[convert_pdf] END: Successfully updated state to DOCX")
    return result
