# src/queues/setup_queue.py
#
# Queue helper for the Setup Agent.
# Enqueues jobs to the "setup" RQ queue.

from typing import Any, Dict, Optional

try:
    from rq import Queue
    _RQ_AVAILABLE = True
except ImportError:
    Queue = None
    _RQ_AVAILABLE = False

from src.queues.redis_client import get_redis

QUEUE_NAME = "setup"


def enqueue_setup_job(payload: Dict[str, Any]) -> Optional[str]:
    """
    Enqueue a setup agent job.

    Returns the RQ job ID if enqueued successfully, None otherwise.
    """
    conn = get_redis()

    if not _RQ_AVAILABLE or conn is None:
        return None

    q = Queue(QUEUE_NAME, connection=conn)
    job = q.enqueue(
        "src.workers.setup_worker.run_graph",
        payload,
    )
    return job.id
