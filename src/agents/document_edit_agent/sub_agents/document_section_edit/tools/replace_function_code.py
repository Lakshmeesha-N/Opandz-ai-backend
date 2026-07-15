# src/agents/document_edit_agent/tools/replace_function_code.py

import json
import asyncio
import logging

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated

logger = logging.getLogger(__name__)


@tool
async def replace_function_code(
    function_name: str,
    new_function_code: str,
    state: Annotated[dict, InjectedState],
) -> dict:
    """
    Replace a function in the current DOCX.js file.
    """

    temp_file_path = state[
        "temp_file_path"
    ]
    logger.info("[replace_function_code] Replacing function %s in file: %s", function_name, temp_file_path)

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/replace_function_code.js",
        temp_file_path,
        function_name,
        new_function_code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        err_msg = stderr.decode()
        logger.error("[replace_function_code] Failed to replace function %s. Error: %s", function_name, err_msg)
        raise ValueError(
            err_msg,
        )

    logger.info("[replace_function_code] Successfully replaced function %s", function_name)
    return json.loads(
        stdout.decode(),
    )