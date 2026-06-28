# src/workers/case_intake_worker.py
#
# RQ worker entrypoint for the Case Intake Agent.
# Run with: rq worker intake

from typing import Dict, Any
import logging

from rq import get_current_job

from src.utils.cleanup import cleanup_temp_file

from src.agents.case_intake_agent.graph import graph as case_intake_graph
from src.core import firebase


def run_intake_graph(payload: Dict[str, Any]):
    """
    Worker entrypoint for running the Case Intake Agent graph.
    Called by the "intake" RQ queue.
    """
    job = get_current_job()
    job_id = job.get_id() if job else None

    firebase.ensure_globals()
    db = firebase.db

    # Seed job document so the API can poll status
    if job_id and db:
        try:
            db.collection("jobs").document(job_id).set(
                {"status": "running", "agent": "intake", "payload": payload}
            )
        except Exception:
            logging.exception("Failed to write initial intake job doc")

    uploaded_files = payload.get("uploaded_files", [])

    try:
        initial_state = {
            "session_id": payload.get("session_id", ""),
            "template_id": payload.get("template_id", ""),
            "field_manifest": {},
            "missing_fields": [],
            "case_data": {},
            "extracted_evidence": [],
            "uploaded_files": uploaded_files,
            "completion_percentage": 0.0,
            "ready_to_generate": False,
            "user_message": payload.get("user_message", ""),
            "chat_history": payload.get("chat_history", []),
            "error": None,
            "next_question": None,
        }

        result = case_intake_graph.invoke(initial_state)

        if job_id and db:
            db.collection("jobs").document(job_id).update(
                {"status": "completed", "result": result}
            )

        return result

    except Exception as e:
        logging.exception("Case intake worker run_intake_graph failed")
        if job_id and db:
            try:
                db.collection("jobs").document(job_id).update(
                    {"status": "failed", "error": str(e)}
                )
            except Exception:
                logging.exception("Failed to write intake job failure doc")
        raise
    finally:
        for file_path in uploaded_files:
            cleanup_temp_file(file_path)
