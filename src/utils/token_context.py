# src/utils/token_context.py
#
# ContextVar-based storage for the "current user" and "current agent" context.
#
# How it works:
#   1. At the start of every authenticated HTTP request (middleware) or
#      background job (worker), call `set_token_context(uid, agent_name)`.
#   2. SharedLLM.invoke() reads these variables automatically and logs
#      token usage to Firestore after every LLM call.
#
# Python's ContextVar is inherently async-safe and thread-safe: each
# concurrent request / asyncio Task / thread gets its own copy of the value.

import contextvars

# ContextVar that holds the Firebase UID of the current user.
# Default is None — meaning no user context is set (e.g. health-check routes).
active_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "active_user_id", default=None
)

# ContextVar that holds the name of the agent currently making LLM calls.
# Example values: "case_intake", "document_generation", "document_edit", "setup"
active_agent_name: contextvars.ContextVar[str] = contextvars.ContextVar(
    "active_agent_name", default="unknown"
)


def set_token_context(uid: str, agent_name: str) -> tuple:
    """
    Set the active user UID and agent name for the current execution context.

    Returns a tuple of (uid_token, agent_token) — the Token objects returned
    by ContextVar.set(). These can be passed to `reset_token_context` to
    restore the previous values if needed (useful for nested contexts).

    Args:
        uid:        Firebase user UID of the authenticated user.
        agent_name: Logical name of the agent making LLM calls
                    (e.g., "case_intake", "document_generation").

    Returns:
        Tuple of ContextVar tokens (uid_token, agent_token).
    """
    uid_token = active_user_id.set(uid)
    agent_token = active_agent_name.set(agent_name)
    return uid_token, agent_token


def reset_token_context(uid_token, agent_token) -> None:
    """
    Reset ContextVars to their previous values using the tokens returned
    by set_token_context(). Call this in a finally block after the job/request
    finishes to ensure the context is clean for the next task on this thread.

    Args:
        uid_token:   Token returned by set_token_context().
        agent_token: Token returned by set_token_context().
    """
    active_user_id.reset(uid_token)
    active_agent_name.reset(agent_token)
