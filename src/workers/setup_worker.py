# src/workers/setup_worker.py
#
# RQ worker entrypoint for the Setup Agent.
# Run with: python -m src.workers.setup_worker
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


def run_graph(payload: Dict[str, Any]):
    """
    Worker entrypoint for running the Setup Agent graph.
    Called by the \"setup\" RQ queue.
    RQ imports this function by dotted path, so the heavy imports below
    must have completed before a job is dispatched — which they will have,
    since they're done synchronously in __main__ before worker.work().
    """
    # These are already imported by the time a job runs (see __main__).
    from rq import get_current_job
    from src.core import firebase
    from src.agents.setup_agent.graph import setup_agent_graph
    from src.utils.cleanup import cleanup_temp_file

    job = get_current_job()
    job_id = job.id if job else None

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
    logging.info("setup-worker: health server bound to port %s", os.environ.get("PORT", "8080"))

    try:
        # ── Step 2: heavy imports (firebase, agent graph) ───────────────────
        logging.info("setup-worker: [1/6] importing config...")
        from src.core.config import settings  # noqa: E402

        logging.info("setup-worker: [2/6] importing agent graph...")
        from src.agents.setup_agent.graph import setup_agent_graph  # noqa: F401,E402

        logging.info("setup-worker: [3/6] importing firebase module...")
        from src.core import firebase  # noqa: E402

        logging.info("setup-worker: [4/6] calling firebase.ensure_globals (firestore)...")
        # Initialize only Firestore first (skip storage to isolate)
        if firebase.db is None:
            firebase.db = firebase.get_firestore()
        logging.info("setup-worker: [4/6] firestore initialized")

        logging.info("setup-worker: [5/6] calling get_storage...")
        if firebase.bucket is None:
            firebase.bucket = firebase.get_storage()
        logging.info("setup-worker: [5/6] storage initialized (bucket=%s)", firebase.bucket)

        logging.info("setup-worker: firebase initialized")

        # ── Step 3: connect to Redis ───────────────────────────────────────
        logging.info("setup-worker: [6/6] connecting to Redis at %s...", settings.redis_url)
        from redis import Redis  # noqa: E402
        from rq import Worker  # noqa: E402
        redis_conn = Redis.from_url(settings.redis_url)
        logging.info("setup-worker: redis connected")

        # ── Step 4: run RQ worker on main thread ────────────────────────────
        worker = Worker(["setup"], connection=redis_conn)
        worker.work()

    except Exception:
        logging.exception("setup-worker: worker crashed — health server stays up")
        # Keep the process alive so Cloud Run doesn't restart-loop instantly.
        threading.Event().wait()
