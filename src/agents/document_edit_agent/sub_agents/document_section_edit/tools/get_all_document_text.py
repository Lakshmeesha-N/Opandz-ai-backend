# src/agents/document_edit_agent/sub_agents/document_section_edit/tools/get_all_document_text.py

import json
import asyncio
import logging

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing import Annotated

logger = logging.getLogger(__name__)


@tool
async def get_all_document_text(
    state: Annotated[dict, InjectedState],
) -> list:
    """
    Returns all visible text in the document, grouped by section (build_* function).

    Each entry in the returned list is:
        { "section": "<function_name>", "text": "<all TextRun strings joined by newline>" }

    IMPORTANT — only call this tool when you genuinely need a full-document
    text scan, for example:
      - The user asks to find or replace a value whose location across sections
        is unknown and get_function_code on individual functions would require
        many guesses.
      - You need to confirm whether a value appears in one section or many
        before deciding which functions to edit.

    Do NOT call this tool when:
      - You already know which function(s) to edit from get_available_functions
        or from context.
      - You only need to inspect one or two specific functions (use
        get_function_code instead — it is cheaper).
    """

    temp_file_path = state["temp_file_path"]

    logger.info(
        "[get_all_document_text] Extracting all text from: %s",
        temp_file_path,
    )

    process = await asyncio.create_subprocess_exec(
        "node",
        "src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/extract_text.js",
        temp_file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        err_msg = stderr.decode()
        logger.error(
            "[get_all_document_text] Failed. Error: %s",
            err_msg,
        )
        raise ValueError(err_msg)

    result = json.loads(stdout.decode())
    logger.info(
        "[get_all_document_text] Extracted text from %d section(s).",
        len(result),
    )
    return result
