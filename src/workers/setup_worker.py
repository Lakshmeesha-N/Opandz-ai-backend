# src/workers/setup_worker.py
#
# RQ worker entrypoint for the Setup Agent.
# Run with: rq worker setup

from typing import Dict, Any
import logging

from rq import get_current_job

from src.agents.setup_agent.graph import setup_agent_graph
from src.core import firebase


def run_graph(payload: Dict[str, Any]):
    """
    Worker entrypoint for running the Setup Agent graph.
    Called by the "setup" RQ queue.
    """
    job = get_current_job()
    job_id = job.get_id() if job else None

    firebase.ensure_globals()
    db = firebase.db

    # Seed job document so the API can poll status
    if job_id and db:
        try:
            db.collection("jobs").document(job_id).set(
                {"status": "running", "agent": "setup", "payload": payload}
            )
        except Exception:
            logging.exception("Failed to write initial job doc")

    try:
        initial_state = {
            "file_path": payload.get("file_path"),
            "file_type": None,
            "docx_blueprint": None,
            "pdf_blueprint": None,
            "lawyer_id": payload.get("lawyer_id"),
            "template_id": payload.get("template_id", ""),
            "error": None,
        }

        result = setup_agent_graph.invoke(initial_state)

        if job_id and db:
            db.collection("jobs").document(job_id).update(
                {"status": "completed", "result": result}
            )

        return result

    except Exception as e:
        logging.exception("Setup worker run_graph failed")
        if job_id and db:
            try:
                db.collection("jobs").document(job_id).update(
                    {"status": "failed", "error": str(e)}
                )
            except Exception:
                logging.exception("Failed to write job failure doc")
        raise
