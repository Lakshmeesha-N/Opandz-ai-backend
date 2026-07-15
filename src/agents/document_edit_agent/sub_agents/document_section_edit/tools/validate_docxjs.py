# src/agents/document_edit_agent/tools/validate_docxjs.py

import json
import asyncio
import logging

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

logger = logging.getLogger(__name__)


@tool
async def validate_docxjs(
    state: Annotated[dict, InjectedState],
) -> dict:
    """
    Validates the current DOCX.js file for JavaScript syntax errors.
    """

    temp_file_path = state[
        "temp_file_path"
    ]
    logger.info("[validate_docxjs] Validating file: %s", temp_file_path)

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/validate_docxjs.js",
        temp_file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        err_msg = stderr.decode()
        logger.error("[validate_docxjs] Validation failed for file %s. Error: %s", temp_file_path, err_msg)
        raise ValueError(
            err_msg,
        )

    logger.info("[validate_docxjs] Validation passed successfully for file: %s", temp_file_path)
    return json.loads(
        stdout.decode(),
    )