from src.core.config import settings
import contextvars
import threading
import queue
import time
import concurrent.futures
import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _create_underlying_client(model_name: Optional[str] = None):
    """Create the provider-specific LLM client (langchain wrappers).
    This mirrors the previous `get_llm` behavior but is used internally
    to back the shared client wrapper.
    """
    target_model = model_name or settings.llm_model

    # --- OpenAI Branch ---
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=target_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    # --- Native Gemini Branch (No OpenAI Wrapping) ---
    elif settings.llm_provider == "gemini":
        if settings.gemini_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=target_model,
                google_api_key=settings.gemini_api_key,
                temperature=0,
                max_output_tokens=20000,
            )
        else:
            if not settings.project_id:
                raise ValueError("project_id must be set in environment or GEMINI_API_KEY must be provided")
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(
                model_name=target_model,
                project=settings.project_id,
                location=settings.gcp_location or "us-central1",
                temperature=0,
                max_output_tokens=8192,
            )

    # --- Ollama Local Branch ---
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=target_model,
            temperature=0.3,
        )


class SharedLLM:
    """Lightweight shared LLM wrapper with background worker and simple batching.

    Provides:
    - `invoke(prompt)` synchronous API (preserves existing nodes)
    - `ainvoke(prompt)` async API for non-blocking calls
    """

    def __init__(self, batch_interval: float = 0.05, batch_size: int = 8, client: Any = None, model_name: Optional[str] = None):
        self._client = client or _create_underlying_client(model_name=model_name)
        self._queue: "queue.Queue[tuple[Any, concurrent.futures.Future]]" = queue.Queue()
        self._batch_interval = batch_interval
        self._batch_size = batch_size
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _call_client(self, prompt: Any) -> Any:
        # Attempt common invocation patterns from langchain wrappers
        try:
            if hasattr(self._client, "invoke"):
                return self._client.invoke(prompt)
            if hasattr(self._client, "generate"):
                return self._client.generate([prompt])
            # fallback to calling the client directly
            return self._client(prompt)
        except Exception:
            # re-raise to be handled by caller
            raise

    def _worker(self):
        while True:
            try:
                first = self._queue.get(block=True)
                if first is None:
                    continue
                batch = [first]
                start = time.time()
                # collect small batch
                while len(batch) < self._batch_size and (time.time() - start) < self._batch_interval:
                    try:
                        item = self._queue.get(block=False)
                        batch.append(item)
                    except queue.Empty:
                        time.sleep(0.001)
                        continue

                # process batch sequentially (preserves order)
                for prompt, fut in batch:
                    if fut.cancelled():
                        continue
                    try:
                        res = self._call_client(prompt)
                        if res and hasattr(res, "content") and isinstance(res.content, list):
                            text_parts = []
                            for part in res.content:
                                if isinstance(part, dict):
                                    text_parts.append(part.get("text", ""))
                                else:
                                    text_parts.append(str(part))
                            res.content = "".join(text_parts)
                        fut.set_result(res)
                    except Exception as e:
                        fut.set_exception(e)
            except Exception:
                # avoid worker crash
                time.sleep(0.1)

    def _log_usage_in_background(self, res: Any) -> None:
        """
        Read token counts from a LangChain response and log them to Firestore
        in a fire-and-forget background thread so the agent is never blocked.
        Also records usage into active TokenTracker context if present.
        """
        try:
            from src.utils.token_context import (
                active_user_id,
                active_agent_name,
                active_token_tracker,
            )
            from src.utils.token_logger import (
                extract_tokens_from_response,
                log_agent_tokens,
            )

            prompt_tokens, completion_tokens = extract_tokens_from_response(res)
            agent_name = active_agent_name.get("unknown")

            tracker = active_token_tracker.get(None)
            if tracker is not None:
                tracker.add_usage(prompt_tokens, completion_tokens, agent_name)

            uid = active_user_id.get(None)
            if not uid:
                # No user context set — skip logging (e.g. health checks)
                return

            if prompt_tokens == 0 and completion_tokens == 0:
                logger.debug(
                    "[SharedLLM] No token counts found in response for uid=%s agent=%s",
                    uid, agent_name,
                )
                return

            # Fire-and-forget: run in a daemon thread so it never blocks the agent
            threading.Thread(
                target=log_agent_tokens,
                args=(uid, agent_name, prompt_tokens, completion_tokens),
                daemon=True,
            ).start()

        except Exception:
            logger.debug("[SharedLLM] Token usage logging failed silently", exc_info=True)

    def invoke(self, prompt: Any, timeout: Optional[float] = None) -> Any:
        """Invoke the client directly, avoiding thread queue issues in spawned processes."""
        res = self._call_client(prompt)
        if res and hasattr(res, "content") and isinstance(res.content, list):
            text_parts = []
            for part in res.content:
                if isinstance(part, dict):
                    text_parts.append(part.get("text", ""))
                else:
                    text_parts.append(str(part))
            res.content = "".join(text_parts)
        # Auto-log token usage for this LLM call
        self._log_usage_in_background(res)
        return res

    async def ainvoke(self, prompt: Any, timeout: Optional[float] = None) -> Any:
        """Async wrapper around `invoke`.

        If called from an asyncio loop, waits without blocking the loop.
        """
        ctx = contextvars.copy_context()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: ctx.run(self.invoke, prompt, timeout))

    def bind_tools(self, tools: list, **kwargs: Any) -> "SharedLLM":
        """Bind tools to the underlying client if supported, returning a new SharedLLM wrapper."""
        if hasattr(self._client, "bind_tools"):
            bound_client = self._client.bind_tools(tools, **kwargs)
            return SharedLLM(
                batch_interval=self._batch_interval,
                batch_size=self._batch_size,
                client=bound_client,
            )
        else:
            raise AttributeError(f"Underlying LLM client {type(self._client)} does not support bind_tools.")


# Cache of SharedLLM instances by model name
_LLM_CACHE: dict[Optional[str], SharedLLM] = {}


def get_llm(model_name: Optional[str] = None) -> SharedLLM:
    """Return a cached SharedLLM wrapper instance for the specified model_name."""
    global _LLM_CACHE
    if model_name not in _LLM_CACHE:
        _LLM_CACHE[model_name] = SharedLLM(model_name=model_name)
    return _LLM_CACHE[model_name]

