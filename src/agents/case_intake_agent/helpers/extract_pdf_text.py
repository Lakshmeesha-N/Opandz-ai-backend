# src/agents/case_intake_agent/helpers/evidence/extract_pdf_text.py

import asyncio
import fitz


async def extract_pdf_text(
    file_path: str,
) -> str:
    """
    Extract text from a PDF.

    Uses PyMuPDF for fast extraction.

    Returns:
        Extracted text as a single string.
    """

    return await asyncio.to_thread(
        _extract_pdf_text_sync,
        file_path,
    )


def _extract_pdf_text_sync(
    file_path: str,
) -> str:
    """
    Synchronous PDF extraction.
    Runs inside a background thread.
    """

    document = fitz.open(file_path)

    pages = []

    try:
        for page in document:
            text = page.get_text("text")

            if text:
                pages.append(text)

        return "\n\n".join(pages)

    finally:
        document.close()