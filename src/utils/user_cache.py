import json
import logging
from typing import Optional
from datetime import datetime
from src.db.models.user import User
from src.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 300


def _user_to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "hashed_password": user.hashed_password,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "api_key": user.api_key,
        "api_key_created_at": user.api_key_created_at.isoformat() if user.api_key_created_at else None,
    }


def _dict_to_user(data: dict) -> User:
    user = User()
    user.id = data["id"]
    user.email = data["email"]
    user.username = data["username"]
    user.hashed_password = data["hashed_password"]
    user.is_active = data["is_active"]
    user.is_superuser = data["is_superuser"]
    user.api_key = data.get("api_key")
    if data.get("api_key_created_at"):
        user.api_key_created_at = datetime.fromisoformat(data["api_key_created_at"])
    return user


def _get_cache_keys(user: User) -> list[str]:
    keys = [
        f"user:id:{user.id}",
        f"user:username:{user.username}",
        f"user:email:{user.email}",
    ]
    if user.api_key:
        keys.append(f"user:apikey:{user.api_key}")
    return keys


def get_cached_user(key: str) -> Optional[User]:
    redis_client = get_redis_client()
    if redis_client is None:
        return None

    try:
        cached_data = redis_client.get(key)
        if cached_data:
            user_dict = json.loads(cached_data)
            return _dict_to_user(user_dict)
    except Exception as e:
        logger.warning(f"Failed to get cached user for key {key}: {e}")

    return None


def set_cached_user(user: User) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return

    try:
        user_dict = _user_to_dict(user)
        user_json = json.dumps(user_dict)

        keys = _get_cache_keys(user)
        pipeline = redis_client.pipeline()
        for key in keys:
            pipeline.setex(key, CACHE_TTL, user_json)
        pipeline.execute()

        logger.debug(f"Cached user {user.username} with {len(keys)} keys")
    except Exception as e:
        logger.warning(f"Failed to cache user {user.username}: {e}")


def invalidate_user_cache(user: User, old_username: Optional[str] = None, old_api_key: Optional[str] = None) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return

    try:
        keys = _get_cache_keys(user)

        if old_username and old_username != user.username:
            keys.append(f"user:username:{old_username}")

        if old_api_key and old_api_key != user.api_key:
            keys.append(f"user:apikey:{old_api_key}")

        if keys:
            redis_client.delete(*keys)
            logger.debug(f"Invalidated {len(keys)} cache keys for user {user.username}")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for user {user.username}: {e}")


def invalidate_user_cache_by_keys(user_id: str, username: str, email: str, api_key: Optional[str] = None) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return

    try:
        keys = [
            f"user:id:{user_id}",
            f"user:username:{username}",
            f"user:email:{email}",
        ]
        if api_key:
            keys.append(f"user:apikey:{api_key}")

        redis_client.delete(*keys)
        logger.debug(f"Invalidated {len(keys)} cache keys for user {username}")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for user {username}: {e}")
