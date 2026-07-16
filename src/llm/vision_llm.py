# src/llm/vision_llm.py

import logging
import threading
from typing import Optional
from src.core.config import settings

logger = logging.getLogger(__name__)


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

    def _log_usage(self, response) -> None:
        """
        Log token usage from a Gemini native SDK response to Firestore.
        Runs in a fire-and-forget background thread so it never blocks.

        The Gemini native SDK stores usage under:
          response.usage_metadata.prompt_token_count
          response.usage_metadata.candidates_token_count
        """
        try:
            from src.utils.token_context import active_user_id, active_agent_name
            from src.utils.token_logger import log_agent_tokens

            uid = active_user_id.get(None)
            if not uid:
                return

            agent_name = active_agent_name.get("unknown")
            usage = getattr(response, "usage_metadata", None)
            if not usage:
                return

            prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
            completion_tokens = getattr(usage, "candidates_token_count", 0) or 0

            if prompt_tokens == 0 and completion_tokens == 0:
                return

            threading.Thread(
                target=log_agent_tokens,
                args=(uid, agent_name, int(prompt_tokens), int(completion_tokens)),
                daemon=True,
            ).start()

        except Exception:
            logger.debug("[VisionLLM] Token usage logging failed silently", exc_info=True)

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

        # Auto-log token usage for this vision LLM call
        self._log_usage(response)

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