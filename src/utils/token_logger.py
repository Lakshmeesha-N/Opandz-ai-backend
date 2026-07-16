# src/utils/token_logger.py
#
# Helper to log LLM token usage to Firestore after each agent run.
# Each call creates an individual log entry so we can query rolling windows.

import logging
from firebase_admin import firestore

logger = logging.getLogger(__name__)


def extract_tokens_from_response(response) -> tuple[int, int]:
    """
    Extract (prompt_tokens, completion_tokens) from a LangChain response object.

    Tries three sources in order:
      1. response.usage_metadata  — standard LangChain >= 0.2 structure
                                    {"input_tokens": ..., "output_tokens": ...}
      2. response.response_metadata["token_usage"] — OpenAI legacy structure
                                    {"prompt_tokens": ..., "completion_tokens": ...}
      3. response.response_metadata["usage_metadata"] — Gemini native structure
                                    {"prompt_token_count": ..., "candidates_token_count": ...}

    Returns (0, 0) if no usage information is found, so callers never crash.

    Args:
        response: Any LangChain BaseMessage (typically an AIMessage).

    Returns:
        Tuple of (prompt_tokens, completion_tokens).
    """
    try:
        # ── 1. Standard LangChain usage_metadata ─────────────────────────────
        usage = getattr(response, "usage_metadata", None)
        if usage and isinstance(usage, dict):
            prompt = usage.get("input_tokens", 0) or 0
            completion = usage.get("output_tokens", 0) or 0
            if prompt or completion:
                return int(prompt), int(completion)

        # ── 2. OpenAI legacy response_metadata["token_usage"] ────────────────
        response_meta = getattr(response, "response_metadata", None) or {}
        token_usage = response_meta.get("token_usage", {})
        if token_usage:
            prompt = token_usage.get("prompt_tokens", 0) or 0
            completion = token_usage.get("completion_tokens", 0) or 0
            if prompt or completion:
                return int(prompt), int(completion)

        # ── 3. Gemini native response_metadata["usage_metadata"] ─────────────
        gemini_usage = response_meta.get("usage_metadata", {})
        if gemini_usage:
            prompt = gemini_usage.get("prompt_token_count", 0) or 0
            completion = gemini_usage.get("candidates_token_count", 0) or 0
            if prompt or completion:
                return int(prompt), int(completion)

    except Exception:
        logger.debug("[token_logger] Could not extract token counts from response", exc_info=True)

    return 0, 0


def log_agent_tokens(
    uid: str,
    agent_name: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """
    Write a single token usage record to the `token_usage` Firestore collection.

    Args:
        uid:               Firebase user UID.
        agent_name:        Name of the agent that made the LLM call
                           (e.g. "case_intake", "document_edit", "setup").
        prompt_tokens:     Number of input/prompt tokens consumed.
        completion_tokens: Number of output/completion tokens generated.
    """
    from src.core.firebase import get_db

    try:
        db = get_db()
        db.collection("token_usage").add(
            {
                "uid": uid,
                "agent": agent_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "timestamp": firestore.SERVER_TIMESTAMP,
            }
        )
        logger.info(
            "[token_logger] Logged %d tokens (prompt=%d, completion=%d) for uid=%s agent=%s",
            prompt_tokens + completion_tokens,
            prompt_tokens,
            completion_tokens,
            uid,
            agent_name,
        )
    except Exception:
        # Never let logging failures break the agent pipeline.
        logger.exception(
            "[token_logger] Failed to log token usage for uid=%s agent=%s",
            uid,
            agent_name,
        )
