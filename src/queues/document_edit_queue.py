# src/queues/document_edit_queue.py
#
# Queue helper for the Document Edit Agent.
# Enqueues jobs to the "document_edit" RQ queue.

from typing import Any, Dict, Optional

try:
    from rq import Queue
    _RQ_AVAILABLE = True
except ImportError:
    Queue = None
    _RQ_AVAILABLE = False

from src.queues.redis_client import get_redis

QUEUE_NAME = "document_edit"


def enqueue_document_edit_job(payload: Dict[str, Any]) -> Optional[str]:
    """
    Enqueue a document edit agent job.

    Returns the RQ job ID if enqueued successfully, None otherwise.
    """
    conn = get_redis()

    if not _RQ_AVAILABLE or conn is None:
        return None

    q = Queue(QUEUE_NAME, connection=conn)
    job = q.enqueue(
        "src.workers.document_edit_worker.run_document_edit_graph",
        payload,
    )
    return job.get_id()
