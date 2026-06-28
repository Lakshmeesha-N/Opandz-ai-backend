# src/agents/case_intake_agent/helpers/evidence/extract_file_content.py

from pathlib import Path

from src.agents.case_intake_agent.helpers.extract_pdf_text import (
    extract_pdf_text,
)

from src.agents.case_intake_agent.helpers.extract_docx_text import (
    extract_docx_text,
)

from src.agents.case_intake_agent.helpers.extract_image_text import (
    extract_image_text,
)


SUPPORTED_IMAGE_TYPES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


async def extract_file_content(
    file_path: str,
) -> dict:
    """
    Extract content from a supported file.

    Returns:
    {
        "file_name": "...",
        "file_type": "...",
        "content": "..."
    }
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    # PDF
    if extension == ".pdf":

        content = await extract_pdf_text(
            file_path
        )

        file_type = "pdf"

    # DOCX
    elif extension == ".docx":

        content = await extract_docx_text(
            file_path
        )

        file_type = "docx"

    # Images
    elif extension in SUPPORTED_IMAGE_TYPES:

        content = await extract_image_text(
            file_path
        )

        file_type = "image"

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    return {
        "file_name": path.name,
        "file_type": file_type,
        "content": content,
    }