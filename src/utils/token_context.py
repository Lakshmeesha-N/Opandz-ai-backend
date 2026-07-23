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
import threading
from typing import Any

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

# ContextVar that holds an active TokenTracker instance if token tracking is enabled.
active_token_tracker: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "active_token_tracker", default=None
)


class TokenTracker:
    """
    Context manager to track LLM token usage during execution.
    """
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.llm_calls = 0
        self.calls_detail = []
        self._lock = threading.Lock()
        self._token = None

    def add_usage(self, prompt_tokens: int, completion_tokens: int, agent_name: str = ""):
        with self._lock:
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            total = prompt_tokens + completion_tokens
            self.total_tokens += total
            self.llm_calls += 1
            self.calls_detail.append({
                "call_index": self.llm_calls,
                "agent": agent_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total,
            })

    def print_summary(self):
        print("\n" + "=" * 55)
        print("              TOKEN USAGE SUMMARY")
        print("=" * 55)
        print(f" Total LLM Calls   : {self.llm_calls}")
        print(f" Prompt Tokens     : {self.prompt_tokens:,}")
        print(f" Completion Tokens : {self.completion_tokens:,}")
        print(f" Total Tokens Used : {self.total_tokens:,}")
        print("=" * 55)
        if self.calls_detail:
            print(" Call Details:")
            for detail in self.calls_detail:
                print(
                    f"   Call #{detail['call_index']} [{detail['agent']}]: "
                    f"Prompt={detail['prompt_tokens']}, "
                    f"Completion={detail['completion_tokens']}, "
                    f"Total={detail['total_tokens']}"
                )
        print("=" * 55 + "\n")

    def __enter__(self):
        self._token = active_token_tracker.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            active_token_tracker.reset(self._token)


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

