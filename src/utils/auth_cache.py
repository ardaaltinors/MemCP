"""
Authentication caching utilities for API key and JWT validation.
Reduces database load by caching user authentication data.
"""
import logging
import json
import uuid
from typing import Optional
from datetime import datetime

from src.utils.redis_client import get_redis_client
from src.db.models.user import User

logger = logging.getLogger(__name__)

# Cache TTL in seconds
API_KEY_CACHE_TTL = 300  # 5 minutes
JWT_USER_CACHE_TTL = 300  # 5 minutes


class AuthCache:
    """
    Handles caching of authentication data to reduce database queries.
    Uses Redis for shared caching across multiple application instances.
    """

    @staticmethod
    def _serialize_user_minimal(user: User) -> str:
        """
        Serialize minimal user data for caching.

        Args:
            user: User model instance

        Returns:
            JSON string with minimal user data
        """
        return json.dumps({
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        })

    @staticmethod
    def _deserialize_user_minimal(data: str) -> dict:
        """
        Deserialize minimal user data from cache.

        Args:
            data: JSON string from cache

        Returns:
            Dictionary with user data
        """
        parsed = json.loads(data)
        parsed["id"] = uuid.UUID(parsed["id"])
        return parsed

    @staticmethod
    def get_user_by_api_key(api_key: str) -> Optional[dict]:
        """
        Get cached user data by API key.

        Args:
            api_key: The API key to lookup

        Returns:
            Dictionary with user data if cached, None otherwise
        """
        try:
            redis_client = get_redis_client()
            cache_key = f"auth:api_key:{api_key}"
            cached = redis_client.get(cache_key)

            if cached:
                logger.debug(f"Cache HIT for API key: {api_key[:10]}...")
                return AuthCache._deserialize_user_minimal(cached)
            else:
                logger.debug(f"Cache MISS for API key: {api_key[:10]}...")
                return None
        except Exception as e:
            logger.warning(f"Redis cache read failed for API key: {e}")
            return None

    @staticmethod
    def set_user_by_api_key(api_key: str, user: User) -> None:
        """
        Cache user data by API key.

        Args:
            api_key: The API key to cache
            user: User model instance to cache
        """
        try:
            redis_client = get_redis_client()
            cache_key = f"auth:api_key:{api_key}"
            serialized = AuthCache._serialize_user_minimal(user)

            redis_client.setex(
                cache_key,
                API_KEY_CACHE_TTL,
                serialized
            )
            logger.debug(f"Cached user for API key: {api_key[:10]}... (TTL: {API_KEY_CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Redis cache write failed for API key: {e}")

    @staticmethod
    def invalidate_user_by_api_key(api_key: str) -> None:
        """
        Invalidate cached user data by API key.
        Use this when an API key is revoked or user is deactivated.

        Args:
            api_key: The API key to invalidate
        """
        try:
            redis_client = get_redis_client()
            cache_key = f"auth:api_key:{api_key}"
            redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for API key: {api_key[:10]}...")
        except Exception as e:
            logger.warning(f"Redis cache invalidation failed for API key: {e}")

    @staticmethod
    def get_user_by_username(username: str) -> Optional[dict]:
        """
        Get cached user data by username (for JWT tokens).

        Args:
            username: The username to lookup

        Returns:
            Dictionary with user data if cached, None otherwise
        """
        try:
            redis_client = get_redis_client()
            cache_key = f"auth:username:{username}"
            cached = redis_client.get(cache_key)

            if cached:
                logger.debug(f"Cache HIT for username: {username}")
                return AuthCache._deserialize_user_minimal(cached)
            else:
                logger.debug(f"Cache MISS for username: {username}")
                return None
        except Exception as e:
            logger.warning(f"Redis cache read failed for username: {e}")
            return None

    @staticmethod
    def set_user_by_username(username: str, user: User) -> None:
        """
        Cache user data by username (for JWT tokens).

        Args:
            username: The username to cache
            user: User model instance to cache
        """
        try:
            redis_client = get_redis_client()
            cache_key = f"auth:username:{username}"
            serialized = AuthCache._serialize_user_minimal(user)

            redis_client.setex(
                cache_key,
                JWT_USER_CACHE_TTL,
                serialized
            )
            logger.debug(f"Cached user for username: {username} (TTL: {JWT_USER_CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Redis cache write failed for username: {e}")

    @staticmethod
    def invalidate_user_by_username(username: str) -> None:
        """
        Invalidate cached user data by username.
        Use this when a user is updated or deactivated.

        Args:
            username: The username to invalidate
        """
        try:
            redis_client = get_redis_client()
            cache_key = f"auth:username:{username}"
            redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for username: {username}")
        except Exception as e:
            logger.warning(f"Redis cache invalidation failed for username: {e}")

    @staticmethod
    def invalidate_all_user_caches(user: User) -> None:
        """
        Invalidate all caches for a user (username + API key).
        Use this when a user is updated, deactivated, or deleted.

        Args:
            user: User model instance
        """
        AuthCache.invalidate_user_by_username(user.username)
        if user.api_key:
            AuthCache.invalidate_user_by_api_key(user.api_key)
        logger.info(f"Invalidated all caches for user: {user.username} (ID: {user.id})")
