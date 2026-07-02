# src/queues/intake_queue.py
#
# Queue helper for the Case Intake Agent.
# Enqueues jobs to the "intake" RQ queue.

from typing import Any, Dict, Optional

try:
    from rq import Queue
    _RQ_AVAILABLE = True
except ImportError:
    Queue = None
    _RQ_AVAILABLE = False

from src.queues.redis_client import get_redis

QUEUE_NAME = "intake"


def enqueue_intake_job(payload: Dict[str, Any]) -> Optional[str]:
    """
    Enqueue a case intake agent job.

    Returns the RQ job ID if enqueued successfully, None otherwise.
    """
    conn = get_redis()

    if not _RQ_AVAILABLE or conn is None:
        return None

    q = Queue(QUEUE_NAME, connection=conn)
    job = q.enqueue(
        "src.workers.case_intake_worker.run_intake_graph",
        payload,
        job_timeout=300,
    )
    return job.id

