"""Tasks package"""
from app.tasks.CeleryWorker import celery_app
from app.tasks.TaskDecorators import single_instance_task

__all__ = [
    'celery_app',
    'single_instance_task'
]
