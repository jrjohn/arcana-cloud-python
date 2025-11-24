"""Tasks package"""
from app.tasks.celery_worker import celery_app
from app.tasks.task_decorators import single_instance_task

__all__ = [
    'celery_app',
    'single_instance_task'
]
