# src/queues/redis_client.py
#
# Single Redis connection shared across all queues and routers.
# Import `redis_conn` wherever you need to enqueue or inspect jobs.

import logging
from typing import Optional

try:
    from redis import Redis
    _REDIS_AVAILABLE = True
except ImportError:
    Redis = None
    _REDIS_AVAILABLE = False

from src.core.config import settings

redis_conn: Optional["Redis"] = None


def get_redis() -> Optional["Redis"]:
    """
    Return the shared Redis connection, creating it on first call.
    Returns None if Redis is not installed or the connection fails.
    """
    global redis_conn

    if not _REDIS_AVAILABLE:
        return None

    if redis_conn is not None:
        return redis_conn

    try:
        redis_conn = Redis.from_url(
            settings.redis_url,
            decode_responses=False,
        )
        redis_conn.ping()  # fail fast if Redis is unreachable
        return redis_conn
    except Exception:
        logging.exception(
            "Redis connection failed – falling back to in-process mode"
        )
        redis_conn = None
        return None
