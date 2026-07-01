# src/workers/document_edit_worker.py
#
# RQ worker entrypoint for the Document Edit Agent.
# Run with: python -m src.workers.document_edit_worker
#
# STARTUP ORDER (critical for Cloud Run health-check):
#   1. Bind port 8080 (health server) — FIRST, before any heavy imports
#   2. Import agent graph + Firebase (may take several seconds on cold start)
#   3. Connect to Redis
#   4. Start RQ worker

import asyncio
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


def save_job_to_firestore(job_id: str, status: str, payload: Dict[str, Any]):
    from src.core import firebase
    firebase.ensure_globals()
    db = firebase.db
    if db:
        try:
            db.collection("jobs").document(job_id).set({
                "status": status,
                "agent": "document_edit",
                "payload": payload,
            })
        except Exception:
            logging.exception("Failed to save job to firestore: %s", job_id)


def update_job_in_firestore(job_id: str, status: str, result: Any = None, error: Any = None):
    from src.core import firebase
    firebase.ensure_globals()
    db = firebase.db
    if db:
        try:
            update_data = {"status": status}
            if result is not None:
                # Strip heavy blueprint fields to prevent redundancy in jobs collection
                if isinstance(result, dict):
                    job_result = {k: v for k, v in result.items() if k not in ("blueprint", "docx_blueprint")}
                else:
                    job_result = result
                from src.agents.setup_agent.utils.template_storage import sanitize_keys
                update_data["result"] = sanitize_keys(job_result)
            if error is not None:
                update_data["error"] = error
            db.collection("jobs").document(job_id).update(update_data)
        except Exception:
            logging.exception("Failed to update job in firestore: %s", job_id)


def run_document_edit_graph(payload: Dict[str, Any]):
    """
    Worker entrypoint for running the Document Edit Agent graph.
    Called by the \"document_edit\" RQ queue.
    """
    from rq import get_current_job
    from src.core import firebase

    job = get_current_job()
    job_id = job.id if job else None

    firebase.ensure_globals()

    return asyncio.run(_run_graph_async(job_id, payload))


async def _run_graph_async(job_id: str, payload: Dict[str, Any]):
    from src.agents.document_edit_agent.graph import graph as document_edit_graph
    from src.agents.document_edit_agent.helpers.redis_store import save_job_result
    from src.utils.cleanup import cleanup_temp_file

    temp_file_path = None
    generated_code = ""
    status = "completed"
    error_msg = None

    # Seed job document so the API can poll status (non-blocking)
    if job_id:
        save_job_result(job_id, "running")
        save_job_to_firestore(job_id, "running", payload)

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
            cleanup_temp_file(temp_file_path)
            for f_path in payload.get("uploaded_files", []):
                cleanup_temp_file(f_path)

        if job_id:
            save_job_result(job_id, status, generated_code, error_msg)
            update_job_in_firestore(job_id, status, result=result)

        return result

    except Exception as e:
        logging.exception("Document edit worker run_graph failed")
        error_msg = str(e)
        if job_id:
            save_job_result(job_id, "failed", "", error_msg)
            update_job_in_firestore(job_id, "failed", error=error_msg)
        raise


# ---------------------------------------------------------------------------
# Health server — only stdlib, binds immediately
# ---------------------------------------------------------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass


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
    logging.info("document-edit-worker: health server bound to port %s", os.environ.get("PORT", "8080"))

    try:
        # ── Step 2: heavy imports (firebase, agent graph) ───────────────────
        logging.info("document-edit-worker: importing agent graph + firebase...")
        from src.core.config import settings  # noqa: E402
        from src.agents.document_edit_agent.graph import graph as document_edit_graph  # noqa: F401,E402
        from src.agents.document_edit_agent.helpers.redis_store import save_job_result  # noqa: F401,E402
        from src.core import firebase  # noqa: E402
        firebase.ensure_globals()
        logging.info("document-edit-worker: firebase initialized")

        # ── Step 3: connect to Redis ─────────────────────────────────────────
        from redis import Redis  # noqa: E402
        from rq import Worker  # noqa: E402
        redis_conn = Redis.from_url(settings.redis_url)
        logging.info("document-edit-worker: redis connected")

        # ── Step 4: run RQ worker on main thread ─────────────────────────────
        worker = Worker(["document_edit"], connection=redis_conn)
        worker.work()

    except Exception:
        logging.exception("document-edit-worker: worker crashed — health server stays up")
        # Keep the process alive so Cloud Run doesn't restart-loop instantly.
        threading.Event().wait()
