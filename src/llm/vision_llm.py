# src/llm/vision_llm.py

from typing import Optional
from src.core.config import settings


class VisionLLM:
    """
    Shared vision client.

    Singleton instance is reused across
    the entire application lifecycle.
    """

    def __init__(self):

        if settings.gemini_api_key:

            from google import genai

            self.client = genai.Client(
                api_key=settings.gemini_api_key
            )

        else:
            raise ValueError(
                "VISION LLM currently requires GEMINI_API_KEY"
            )

        self.model = settings.vision_llm_model

    def extract_image(
        self,
        image_bytes: bytes,
        prompt: str,
    ) -> str:
        """
        Extract information from image.
        """

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_bytes,
                },
            ],
        )

        return response.text

    async def aextract_image(
        self,
        image_bytes: bytes,
        prompt: str,
    ) -> str:

        import asyncio

        return await asyncio.to_thread(
            self.extract_image,
            image_bytes,
            prompt,
        )


# ----------------------------------
# Singleton
# ----------------------------------

_SHARED_VISION_LLM: Optional[
    VisionLLM
] = None


def get_vision_llm() -> VisionLLM:
    """
    Shared vision model instance.
    """

    global _SHARED_VISION_LLM

    if _SHARED_VISION_LLM is None:
        _SHARED_VISION_LLM = VisionLLM()

    return _SHARED_VISION_LLM