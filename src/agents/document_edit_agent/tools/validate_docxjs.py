# src/agents/document_edit_agent/tools/validate_docxjs.py

import json
import asyncio

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState


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

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/scripts/validate_docxjs.js",
        temp_file_path,
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