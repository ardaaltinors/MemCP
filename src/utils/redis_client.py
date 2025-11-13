import os
import logging
from typing import Optional
import redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisClient:
    _instance: Optional[redis.Redis] = None
    _pool: Optional[ConnectionPool] = None
    _enabled: bool = True

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        if not cls._enabled:
            return None

        if cls._instance is None:
            try:
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))

                cls._pool = ConnectionPool(
                    host=redis_host,
                    port=redis_port,
                    db=1,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    max_connections=10,
                )

                cls._instance = redis.Redis(connection_pool=cls._pool)

                cls._instance.ping()
                logger.info(f"Redis cache client initialized successfully (DB 1) at {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis cache unavailable, falling back to database only: {e}")
                cls._enabled = False
                cls._instance = None
                return None

        return cls._instance

    @classmethod
    def is_available(cls) -> bool:
        if not cls._enabled:
            return False

        client = cls.get_client()
        if client is None:
            return False

        try:
            client.ping()
            return True
        except Exception:
            logger.warning("Redis connection lost, disabling cache")
            cls._enabled = False
            cls._instance = None
            return False

    @classmethod
    def reset(cls):
        if cls._instance:
            try:
                cls._instance.close()
            except Exception:
                pass
        if cls._pool:
            try:
                cls._pool.disconnect()
            except Exception:
                pass
        cls._instance = None
        cls._pool = None
        cls._enabled = True


def get_redis_client() -> Optional[redis.Redis]:
    return RedisClient.get_client()
