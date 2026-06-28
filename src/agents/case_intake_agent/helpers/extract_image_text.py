# src/agents/case_intake_agent/helpers/evidence/extract_image_text.py

from pathlib import Path

from src.llm.vision_llm import get_vision_llm


EXTRACTION_PROMPT = """
You are a legal document extraction system.

Extract ALL visible information from the image.

Rules:
1. Extract all text exactly as seen.
2. Preserve numbers, dates, addresses, IDs, and names.
3. Do not summarize.
4. Do not omit fields.
5. If the document contains tables, extract them.
6. Return plain text only.
7. If the image is unclear, extract whatever is readable.
"""


async def extract_image_text(
    file_path: str,
) -> str:
    """
    Extract text from an image using the shared vision model.

    Supports:
    - jpg
    - jpeg
    - png
    - webp
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {file_path}"
        )

    with open(path, "rb") as file:
        image_bytes = file.read()

    vision_llm = get_vision_llm()

    extracted_text = await vision_llm.aextract_image(
        image_bytes=image_bytes,
        prompt=EXTRACTION_PROMPT,
    )

    return extracted_text