# src/workers/unified_worker.py
#
# Unified RQ worker entrypoint listening to setup, intake, and document_edit queues.
# Binds a single health check port and runs on a single container instance/GPU.

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 1. Bind health check port immediately
    threading.Thread(target=run_health_server, daemon=True).start()
    logging.info("unified-worker: health server bound to port %s", os.environ.get("PORT", "8080"))

    try:
        # 2. Imports
        from src.core.config import settings
        from src.core import firebase
        
        # Ensure firebase is initialized
        firebase.ensure_globals()
        if firebase.db is None:
            firebase.db = firebase.get_firestore()
        if firebase.bucket is None:
            firebase.bucket = firebase.get_storage()
            
        # Eagerly import all agent graphs to cache them
        try:
            from src.agents.setup_agent.graph import setup_agent_graph
            from src.agents.case_intake_agent.graph import graph as case_intake_graph
            from src.agents.document_edit_agent.graph import document_edit_agent_graph
            logging.info("unified-worker: all agent graphs eagerly loaded")
        except Exception:
            logging.exception("Failed to eagerly load some graphs")

        # 3. Connect to Redis
        from redis import Redis
        from rq import Worker
        redis_conn = Redis.from_url(settings.redis_url)
        logging.info("unified-worker: redis connected")

        # 4. Start worker listening to all three queues
        queues = ["setup", "intake", "document_edit"]
        logging.info("unified-worker: starting RQ worker listening to queues: %s", queues)
        worker = Worker(queues, connection=redis_conn)
        worker.work()

    except Exception:
        logging.exception("unified-worker: worker crashed — health server stays up")
        threading.Event().wait()
