# src/agents/case_intake_agent/helpers/extract_all_evidence.py

import asyncio

from src.agents.case_intake_agent.helpers.extract_file_content import (
    extract_file_content,
)


async def extract_all_evidence(
    uploaded_files: list[str],
) -> list[dict]:
    """
    Extract evidence from all uploaded files concurrently.
    """

    if not uploaded_files:
        return []

    tasks = [
        extract_file_content(file_path)
        for file_path in uploaded_files
    ]

    return await asyncio.gather(*tasks)