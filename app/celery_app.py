"""
Celery Application Configuration

This module configures Celery for asynchronous task processing
with Redis as the message broker and result backend.
"""

from celery import Celery
from .config import settings
import os

# Get Redis configuration from settings or environment
redis_host = os.getenv("REDIS_HOST", settings.redis_host)
redis_port = os.getenv("REDIS_PORT", settings.redis_port)

# Initialize Celery application
celery_app = Celery(
    "document_agent",
    broker=f"redis://{redis_host}:{redis_port}/1",
    backend=f"redis://{redis_host}:{redis_port}/2",
    include=["app.tasks"]  # Explicitly include tasks module
)

# Celery configuration
celery_app.conf.update(
    # Task configuration
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,
    task_time_limit=300,  # Hard time limit of 5 minutes per task
    task_soft_time_limit=270,  # Soft time limit of 4.5 minutes
    task_acks_late=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Timezone configuration
    timezone="UTC",
    enable_utc=True,
    
    # Beat schedule (if needed for periodic tasks)
    beat_schedule={},
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
)

# Auto-discover tasks from the tasks module
celery_app.autodiscover_tasks()

# Import worker signals to register them
# This must be done after celery_app is created but before workers start
try:
    from . import worker_signals
except ImportError:
    # Signals are optional - if not present, continue without them
    pass

# For debugging - print configuration
if settings.debug:
    print(f"Celery configured with broker: redis://{redis_host}:{redis_port}/1")
    print(f"Celery configured with backend: redis://{redis_host}:{redis_port}/2")