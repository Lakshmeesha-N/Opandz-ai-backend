# src/utils/token_logger.py
#
# Helper to log LLM token usage to Firestore after each agent run.
# Each call creates an individual log entry so we can query rolling windows.

import logging
from firebase_admin import firestore

logger = logging.getLogger(__name__)


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
