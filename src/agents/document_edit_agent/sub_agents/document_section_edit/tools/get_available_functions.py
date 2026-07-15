# src/agents/document_edit_agent/tools/get_available_functions.py

import json
import asyncio

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated


@tool
async def get_available_functions(
    state: Annotated[dict, InjectedState],
) -> list[dict]:
    """
    Returns all available functions from the current DOCX.js file.
    """

    temp_file_path = state[
        "temp_file_path"
    ]

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/parser_ast.js",
        temp_file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:

        raise ValueError(
            stderr.decode(),
        )

    ast_result = json.loads(
        stdout.decode(),
    )

    return [
        {
            "name": function["name"],
        }
        for function in ast_result.get(
            "functions",
            [],
        )
        if function.get(
            "name",
        )
    ]