# src/agents/document_edit_agent/helpers/redis_store.py

import json
import logging
from typing import Optional, Dict, Any
from src.queues.redis_client import get_redis

def save_job_result(job_id: str, status: str, generated_docxjs_code: str = "", error: Optional[str] = None, agent_output: Optional[str] = None) -> None:
    """
    Saves the job result/status to Redis with a TTL of 1 hour.
    """
    conn = get_redis()
    if conn:
        try:
            data = {
                "status": status,
                "generated_docxjs_code": generated_docxjs_code,
                "error": error or "",
                "agent_output": agent_output or ""
            }
            key = f"document_edit:result:{job_id}"
            conn.setex(key, 3600, json.dumps(data))
            logging.info("Saved job result to Redis for job %s: status=%s", job_id, status)
        except Exception:
            logging.exception("Failed to save job result to Redis for job %s", job_id)

def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the job result/status from Redis.
    """
    conn = get_redis()
    if conn:
        try:
            key = f"document_edit:result:{job_id}"
            data = conn.get(key)
            if data:
                return json.loads(data)
        except Exception:
            logging.exception("Failed to get job result from Redis for job %s", job_id)
    return None

def delete_job_result(
    job_id: str,
) -> None:

    conn = get_redis()

    if conn:

        try:

            key = (
                f"document_edit:result:{job_id}"
            )

            conn.delete(
                key,
            )

            logging.info(
                "Deleted Redis job result %s",
                job_id,
            )

        except Exception:

            logging.exception(
                "Failed to delete Redis job result %s",
                job_id,
            )