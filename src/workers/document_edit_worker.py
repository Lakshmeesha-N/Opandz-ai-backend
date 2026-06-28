# src/workers/document_edit_worker.py
#
# RQ worker entrypoint for the Document Edit Agent.
# Run with: rq worker document_edit

import asyncio
import os
from typing import Dict, Any
import logging

from rq import get_current_job

from src.agents.document_edit_agent.graph import graph as document_edit_graph
from src.utils.cleanup import cleanup_temp_file
from src.agents.document_edit_agent.helpers.redis_store import (
    save_job_result,
    save_job_to_firestore,
    update_job_in_firestore,
)
from src.core import firebase


def run_document_edit_graph(payload: Dict[str, Any]):
    """
    Worker entrypoint for running the Document Edit Agent graph.
    Called by the "document_edit" RQ queue.
    """
    job = get_current_job()
    job_id = job.get_id() if job else None

    firebase.ensure_globals()

    # We will invoke the async graph in an event loop
    return asyncio.run(_run_graph_async(job_id, payload))


async def _run_graph_async(job_id: str, payload: Dict[str, Any]):
    temp_file_path = None
    generated_code = ""
    status = "completed"
    error_msg = None

    # Seed job document so the API can poll status (non-blocking)
    if job_id:
        await save_job_result(job_id, "running")
        await save_job_to_firestore(job_id, "running", payload)

    try:
        initial_state = {
            "lawyer_id": payload.get("lawyer_id", ""),
            "template_id": payload.get("template_id", ""),
            "user_message": payload.get("user_message", ""),
            "temp_file_path": "",
            "document_config": {},
            "blueprint": {},
            "messages": payload.get("messages", []),
            "uploaded_files": payload.get("uploaded_files", []),
            "error": None,
        }

        # The function that calls graph.ainvoke(state) must wrap the invocation in a try/finally block
        result = None
        try:
            result = await document_edit_graph.ainvoke(initial_state)
            if result:
                if "temp_file_path" in result:
                    temp_file_path = result["temp_file_path"]
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            with open(temp_file_path, "r", encoding="utf-8") as f:
                                generated_code = f.read()
                        except Exception:
                            logging.exception("Failed to read temporary DOCX.js file")
                if result.get("error"):
                    error_msg = result["error"]
                    status = "failed"
        finally:
            # After graph.ainvoke() returns (or raises an exception), read state["temp_file_path"]
            # from the returned state and delete the file if it exists.
            cleanup_temp_file(temp_file_path)
            for f_path in payload.get("uploaded_files", []):
                cleanup_temp_file(f_path)

        if job_id:
            await save_job_result(job_id, status, generated_code, error_msg)
            await update_job_in_firestore(job_id, status, result=result)

        return result

    except Exception as e:
        logging.exception("Document edit worker run_graph failed")
        error_msg = str(e)
        if job_id:
            await save_job_result(job_id, "failed", "", error_msg)
            await update_job_in_firestore(job_id, "failed", error=error_msg)
        raise

