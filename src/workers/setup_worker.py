# src/workers/setup_worker.py
#
# RQ worker entrypoint for the Setup Agent.
# Run with: python -m src.workers.setup_worker

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any
import logging

from rq import get_current_job, Worker
from redis import Redis

from src.agents.setup_agent.graph import setup_agent_graph
from src.core import firebase
from src.utils.cleanup import cleanup_temp_file


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
    finally:
        cleanup_temp_file(payload.get("file_path"))


# ---------------------------------------------------------------------------
# Cloud Run requires the container to bind to $PORT.
# HTTP server starts FIRST so the health-check always responds.
# ---------------------------------------------------------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
    def log_message(self, format, *args):
        pass  # silence access logs

def run_health_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        from src.core.config import settings

        # Start health server FIRST so Cloud Run health-check always succeeds
        # even if Redis/RQ startup is slow.
        threading.Thread(target=run_health_server, daemon=True).start()
        logging.info("setup-worker: health server running, starting RQ worker...")

        redis_conn = Redis.from_url(settings.redis_url)

        # Run RQ worker on main thread
        worker = Worker(["setup"], connection=redis_conn)
        worker.work()
    except Exception:
        logging.exception("setup-worker: worker crashed")
