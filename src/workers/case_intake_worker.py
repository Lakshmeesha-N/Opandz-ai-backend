# src/workers/case_intake_worker.py
#
# RQ worker entrypoint for the Case Intake Agent.
# Run with: python -m src.workers.case_intake_worker

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any
import logging

from rq import get_current_job, Worker
from redis import Redis

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


# ---------------------------------------------------------------------------
# Cloud Run requires the container to bind to $PORT.
# HTTP server starts FIRST so the health-check always responds.
# The RQ worker runs in a daemon thread; any startup failure there
# is logged but does NOT prevent the health-check from binding.
# ---------------------------------------------------------------------------
class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):  # silence access logs
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def _run_worker():
        try:
            from src.core.config import settings
            redis_conn = Redis.from_url(settings.redis_url)
            worker = Worker(["intake"], connection=redis_conn)
            logging.info("intake-worker: connected to Redis, starting worker loop")
            worker.work()
        except Exception:
            logging.exception("intake-worker: worker thread crashed — health-check still running")

    t = threading.Thread(target=_run_worker, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", "8080"))
    logging.info("intake-worker: serving health-check on port %s", port)
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()
