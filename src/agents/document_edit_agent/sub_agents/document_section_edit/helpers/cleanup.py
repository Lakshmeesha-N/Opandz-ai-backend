# src/agents/document_edit_agent/helpers/cleanup.py

import os
import logging
from typing import Optional

def cleanup_temp_file(temp_file_path: Optional[str]) -> None:
    """
    Safely removes a temporary file if it exists.
    """
    if not temp_file_path:
        return
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info("Successfully cleaned up temporary DOCX.js file: %s", temp_file_path)
    except Exception as e:
        logging.exception("Failed to cleanup temporary file %s: %s", temp_file_path, e)
