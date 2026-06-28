# src/agents/document_edit_agent/tools/replace_function_code.py

import json
import asyncio

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated


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

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/scripts/replace_function_code.js",
        temp_file_path,
        function_name,
        new_function_code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:

        raise ValueError(
            stderr.decode(),
        )

    return json.loads(
        stdout.decode(),
    )