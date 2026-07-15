# src/agents/document_edit_agent/sub_agents/document_section_edit/tools/replace_multiple_functions_code.py

import json
import asyncio
import logging

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated

logger = logging.getLogger(__name__)


@tool
async def replace_multiple_functions_code(
    replacements: list[dict],
    state: Annotated[dict, InjectedState],
) -> dict:
    """
    Atomically replace one or more functions in the current DOCX.js file.

    Use this tool whenever you need to edit functions in the document — whether
    that is one function or many. All replacements are applied in a single
    read-write cycle, so no edit can overwrite another.

    Args:
        replacements: A list of objects, each with:
            - function_name (str): The exact name of the JS function to replace.
            - new_function_code (str): The complete new source code for that function.

    Returns:
        A dict with { success: true, replaced: [<function names>] }.
    """

    temp_file_path = state["temp_file_path"]

    # Normalise key names: the LLM sends function_name / new_function_code,
    # but the JS script expects { name, code }.
    normalised = []
    for item in replacements:
        fn_name = item.get("function_name") or item.get("name")
        fn_code = item.get("new_function_code") or item.get("code")
        if not fn_name or fn_code is None:
            raise ValueError(
                "Each replacement must have 'function_name' and 'new_function_code'."
            )
        normalised.append({"name": fn_name, "code": fn_code})

    logger.info(
        "[replace_multiple_functions_code] Replacing %d function(s) in %s: %s",
        len(normalised),
        temp_file_path,
        [r["name"] for r in normalised],
    )

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/replace_multiple_functions_code.js",
        temp_file_path,
        json.dumps(normalised),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        err_msg = stderr.decode()
        logger.error(
            "[replace_multiple_functions_code] Failed. Error: %s",
            err_msg,
        )
        raise ValueError(err_msg)

    result = json.loads(stdout.decode())
    logger.info(
        "[replace_multiple_functions_code] Successfully replaced: %s",
        result.get("replaced"),
    )
    return result
