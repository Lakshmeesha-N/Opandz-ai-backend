from src.core.config import settings
import threading
import queue
import time
import concurrent.futures
import asyncio
from typing import Any, Optional


def _create_underlying_client():
    """Create the provider-specific LLM client (langchain wrappers).
    This mirrors the previous `get_llm` behavior but is used internally
    to back the shared client wrapper.
    """
    # --- OpenAI Branch ---
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )

    # --- Native Gemini Branch (No OpenAI Wrapping) ---
    elif settings.llm_provider == "gemini":
        if settings.gemini_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.gemini_api_key,
                temperature=0,
            )
        else:
            if not settings.project_id:
                raise ValueError("project_id must be set in environment or GEMINI_API_KEY must be provided")
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(
                model_name=settings.llm_model,
                project=settings.project_id,
                location=settings.gcp_location or "us-central1",
                temperature=0,
            )

    # --- Ollama Local Branch ---
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.llm_model,
            temperature=0.3,
        )


class SharedLLM:
    """Lightweight shared LLM wrapper with background worker and simple batching.

    Provides:
    - `invoke(prompt)` synchronous API (preserves existing nodes)
    - `ainvoke(prompt)` async API for non-blocking calls
    """

    def __init__(self, batch_interval: float = 0.05, batch_size: int = 8, client: Any = None):
        self._client = client or _create_underlying_client()
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

    def invoke(self, prompt: Any, timeout: Optional[float] = None) -> Any:
        """Synchronous invoke used by existing nodes.

        Submits the prompt to the background worker and waits for the result.
        """
        fut = concurrent.futures.Future()
        self._queue.put((prompt, fut))
        return fut.result(timeout=timeout)

    async def ainvoke(self, prompt: Any, timeout: Optional[float] = None) -> Any:
        """Async wrapper around `invoke`.

        If called from an asyncio loop, waits without blocking the loop.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.invoke, prompt, timeout)

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


# Singleton shared LLM instance
_SHARED_LLM: Optional[SharedLLM] = None


def get_llm() -> SharedLLM:
    """Return the shared LLM wrapper instance."""
    global _SHARED_LLM
    if _SHARED_LLM is None:
        _SHARED_LLM = SharedLLM()
    return _SHARED_LLM

