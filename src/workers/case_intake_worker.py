# src/workers/case_intake_worker.py
#
# RQ worker entrypoint for the Case Intake Agent.
# Run with: python -m src.workers.case_intake_worker
#
# STARTUP ORDER (critical for Cloud Run health-check):
#   1. Bind port 8080 (health server) — FIRST, before any heavy imports
#   2. Import agent graph + Firebase (may take several seconds on cold start)
#   3. Connect to Redis
#   4. Start RQ worker

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Lightweight stdlib-only types — safe to import at module level.
# Heavy imports (agent graphs, firebase, redis) are deferred to __main__
# so they NEVER block the health-check port from binding.
# ---------------------------------------------------------------------------


def run_intake_graph(payload: Dict[str, Any]):
    """
    Worker entrypoint for running the Case Intake Agent graph.
    Called by the \"intake\" RQ queue.
    """
    from rq import get_current_job
    from src.core import firebase
    from src.agents.case_intake_agent.graph import graph as case_intake_graph
    from src.utils.cleanup import cleanup_temp_file

    job = get_current_job()
    job_id = job.id if job else None

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
            job_result = {k: v for k, v in result.items() if k not in ("blueprint", "docx_blueprint")}
            from src.agents.setup_agent.utils.template_storage import sanitize_keys
            sanitized_result = sanitize_keys(job_result)
            db.collection("jobs").document(job_id).update(
                {"status": "completed", "result": sanitized_result}
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
# Health server — only stdlib, binds immediately
# ---------------------------------------------------------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass  # silence access logs


def run_health_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # ── Step 1: bind port 8080 IMMEDIATELY (before ANY heavy import) ────────
    threading.Thread(target=run_health_server, daemon=True).start()
    logging.info("intake-worker: health server bound to port %s", os.environ.get("PORT", "8080"))

    try:
        # ── Step 2: heavy imports (firebase, agent graph) ───────────────────
        logging.info("intake-worker: importing agent graph + firebase...")
        from src.core.config import settings  # noqa: E402
        from src.agents.case_intake_agent.graph import graph as case_intake_graph  # noqa: F401,E402
        from src.core import firebase  # noqa: E402
        firebase.ensure_globals()
        logging.info("intake-worker: firebase initialized")

        # ── Step 3: connect to Redis ─────────────────────────────────────────
        from redis import Redis  # noqa: E402
        from rq import Worker  # noqa: E402
        redis_conn = Redis.from_url(settings.redis_url)
        logging.info("intake-worker: redis connected")

        # ── Step 4: run RQ worker on main thread ─────────────────────────────
        worker = Worker(["intake"], connection=redis_conn)
        worker.work()

    except Exception:
        logging.exception("intake-worker: worker crashed — health server stays up")
        # Keep the process alive so Cloud Run doesn't restart-loop instantly.
        threading.Event().wait()
