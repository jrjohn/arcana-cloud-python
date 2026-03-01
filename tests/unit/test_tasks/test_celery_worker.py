"""
Celery Worker Unit Tests
Tests for app/tasks/celery_worker.py
"""
import pytest
from unittest.mock import patch, MagicMock


class TestDebugTask:
    """Tests for debug_task – line 85"""

    def test_debug_task_executes(self):
        """Line 85: print(f'Request: {self.request!r}')"""
        from app.tasks.celery_worker import debug_task

        # Call the task's underlying function with a mock self
        # debug_task.run() passes the task instance as self for bind=True tasks
        with patch('builtins.print') as mock_print:
            debug_task.run()

        # Verify print was called (line 85 executed)
        mock_print.assert_called_once()

    def test_debug_task_is_registered(self):
        """Verify debug_task is a registered Celery task"""
        from app.tasks.celery_worker import debug_task, celery_app
        assert debug_task.name is not None

    def test_celery_app_configured(self):
        """Verify Celery app configuration is loaded"""
        from app.tasks.celery_worker import celery_app
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.timezone == 'UTC'
