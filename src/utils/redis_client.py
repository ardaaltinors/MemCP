"""
Shared Redis client for caching across the application.
"""
import os
import logging
from typing import Optional
import redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)

# Global connection pool (singleton)
_redis_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """
    Get or create the Redis connection pool.
    Uses a singleton pattern to ensure only one pool exists.
    """
    global _redis_pool

    if _redis_pool is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        _redis_pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            db=1,  # Use DB 1 for caching (DB 0 is for Celery)
            decode_responses=True,  # Auto-decode bytes to strings
            max_connections=50,  # Connection pool size
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        logger.info(f"Redis connection pool initialized: {redis_host}:{redis_port} (db=1)")

    return _redis_pool


def get_redis_client() -> redis.Redis:
    """
    Get a Redis client from the connection pool.

    Returns:
        Redis client instance with connection pooling
    """
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)
