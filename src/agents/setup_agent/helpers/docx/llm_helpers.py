# helpers/llm_helpers.py

import logging
import os
import time

from src.llm.llm import get_llm

logger = logging.getLogger(__name__)


def read_file(path: str) -> str:
    """Read a file and return its contents, or empty string if not found."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    logger.warning("[llm_helpers] File not found: %s", path)
    return ""


def extract_section_metadata(blueprint: dict) -> list:
    """Extract section_id and metadata from the parsed blueprint dict."""
    sections = blueprint.get("sections", [])
    extracted = []
    for section in sections:
        extracted.append({
            "section_id": section.get("section_id"),
            "metadata": section.get("metadata", {}),
        })
    return extracted


def invoke_llm_with_retries(prompt: str, max_retries: int = 3) -> str:
    """Invoke the LLM with exponential-backoff retries."""
    llm = get_llm()
    response = None
    for attempt in range(1, max_retries + 1):
        try:
            response = llm.invoke(prompt)
            break
        except Exception as e:
            logger.warning(
                "[llm_helpers] LLM attempt %d/%d failed: %s",
                attempt, max_retries, e,
            )
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)

    # Resolve response to string
    if isinstance(response, str):
        text = response
    else:
        text = getattr(response, "content", str(response))

    # Handle list-of-parts responses
    if isinstance(text, list):
        parts = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
        text = "".join(parts)

    return text


def clean_markdown_text(text: str) -> str:
    """Clean markdown text by stripping code block fences if wrapped by LLM."""
    if not text:
        return ""
    cleaned = text.strip()
    import re
    cleaned = re.sub(r"^```(?:markdown)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?\s*```$", "", cleaned)
    return cleaned.strip()

