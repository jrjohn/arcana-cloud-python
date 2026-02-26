"""
Celery Worker Configuration
Celery application configuration and initialization
"""
import os
from celery import Celery
from celery.schedules import crontab

# Default Redis URL constant (SonarQube S1192)
DEFAULT_REDIS_URL = 'redis://localhost:6379/0'

# Create Celery application
celery_app = Celery(
    'arcana_cloud',
    broker=os.getenv('CELERY_BROKER_URL', DEFAULT_REDIS_URL),
    backend=os.getenv('CELERY_RESULT_BACKEND', DEFAULT_REDIS_URL)
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task result configuration
    result_expires=3600,  # Result retention 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },

    # Task execution configuration
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task when worker is lost
    task_track_started=True,  # Track task start status

    # Worker configuration
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=1000,  # Each worker subprocess restarts after executing maximum 1000 tasks

    # Beat scheduler configuration (using RedBeat)
    beat_scheduler='redbeat.RedBeatScheduler',
    redbeat_redis_url=os.getenv('CELERY_BROKER_URL', DEFAULT_REDIS_URL),
    redbeat_key_prefix='celery:beat:',

    # Task routing
    task_routes={
        'app.tasks.ScheduledTasks.*': {'queue': 'scheduled'},
        'app.tasks.BackgroundTasks.*': {'queue': 'background'},
    },
)

# Scheduled task configuration
celery_app.conf.beat_schedule = {
    # Clean up expired tokens daily at 2 AM
    'cleanup-expired-tokens': {
        'task': 'app.tasks.ScheduledTasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),
    },
    # Execute health check every hour
    'health-check': {
        'task': 'app.tasks.ScheduledTasks.health_check_task',
        'schedule': crontab(minute=0),
    },
    # Generate statistics report every 10 minutes
    'generate-stats': {
        'task': 'app.tasks.ScheduledTasks.generate_statistics',
        'schedule': crontab(minute='*/10'),
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks([
    'app.tasks.ScheduledTasks',
    'app.tasks.BackgroundTasks'
])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')
