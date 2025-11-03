import os
from dotenv import load_dotenv
from celery import Celery
from src.exceptions import ConfigurationError

load_dotenv()

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
    task_acks_late=True,  # Acknowledge task after completion, not before
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=360,  # 6 minutes hard limit
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    broker_transport_options={
        'visibility_timeout': 400,  # Must be longer than task_time_limit
        'fanout_prefix': True,
        'fanout_patterns': True
    },
    # Singleton configuration
    singleton_key_prefix='celery_singleton',  # Prefix for lock keys
    task_ignore_result=False,  # Required for singleton to work
) 