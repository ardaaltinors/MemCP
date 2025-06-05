import contextvars
from contextlib import contextmanager
from typing import Optional
import uuid

# Context variable for the current user_id (async-safe)
_current_user_id: contextvars.ContextVar[Optional[uuid.UUID]] = contextvars.ContextVar(
    'current_user_id', default=None
)


def set_current_user_id(user_id: uuid.UUID) -> None:
    """Set the current user_id for this async context."""
    _current_user_id.set(user_id)


def get_current_user_id() -> Optional[uuid.UUID]:
    """Get the current user_id for this async context."""
    return _current_user_id.get()


@contextmanager
def user_context(user_id: uuid.UUID):
    """Context manager to set the current user_id for the duration of the context."""
    token = _current_user_id.set(user_id)
    try:
        yield
    finally:
        _current_user_id.reset(token) 