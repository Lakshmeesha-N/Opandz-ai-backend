# nodes/clean_temp.py

import logging
import os
import shutil

from src.agents.setup_agent.schema.global_state import AgentState

logger = logging.getLogger(__name__)


def clean_temp(state: AgentState) -> AgentState:
    """
    Delete the temporary directory used for unzipped DOCX files and
    intermediate markdown outputs.

    This node runs at the END of both the success path and the error
    path so that temp files are always cleaned up.
    """

    temp_dir = state.get("temp_dir")

    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.info(
                "[clean_temp] Deleted temp directory: %s", temp_dir
            )
        except Exception as e:
            # Log but don't fail the graph — cleanup is best-effort
            logger.warning(
                "[clean_temp] Failed to delete temp directory %s: %s",
                temp_dir,
                str(e),
            )
    else:
        logger.info(
            "[clean_temp] No temp directory to clean (temp_dir=%s)",
            temp_dir,
        )

    return {"temp_dir": None}
