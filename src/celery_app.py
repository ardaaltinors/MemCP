import os
from celery import Celery
from src.exceptions import ConfigurationError

# Get broker URL from environment variables
broker_url = os.getenv("CELERY_BROKER_URL")
if not broker_url:
    raise ConfigurationError(
        message="Celery broker URL is not configured.",
        config_key="CELERY_BROKER_URL",
        expected_type="string"
    )

# Get result backend from environment variables
result_backend = os.getenv("CELERY_RESULT_BACKEND")
if not result_backend:
    raise ConfigurationError(
        message="Celery result backend is not configured.",
        config_key="CELERY_RESULT_BACKEND",
        expected_type="string"
    )

celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=result_backend,
    include=["src.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
) 