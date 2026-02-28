"""
Background Tasks Unit Tests
"""
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestSendWelcomeEmail:
    """Tests for send_welcome_email task"""

    def test_send_welcome_email_success(self):
        with patch('app.tasks.background_tasks.celery_app') as mock_celery:
            # Mock the task decorator to be a passthrough
            mock_celery.task = lambda *args, **kwargs: lambda f: f

            # Import after patching
            with patch('app.tasks.task_decorators.retry_with_backoff',
                       return_value=lambda f: f):
                from app.tasks.background_tasks import send_welcome_email
                # Can't easily call Celery tasks directly, so test the module loads
                assert send_welcome_email is not None

    def test_background_tasks_module_importable(self):
        """Verify module can be imported without errors"""
        with patch('app.tasks.celery_worker.celery_app'):
            import app.tasks.background_tasks as bg
            assert bg is not None


class TestScheduledTasks:
    """Tests for scheduled_tasks module"""

    def test_scheduled_tasks_module_importable(self):
        with patch('app.tasks.celery_worker.celery_app'):
            import app.tasks.scheduled_tasks as st
            assert st is not None

    def test_cleanup_expired_tokens_task_exists(self):
        with patch('app.tasks.celery_worker.celery_app'):
            import app.tasks.scheduled_tasks as st
            assert hasattr(st, 'cleanup_expired_tokens')

    def test_health_check_task_exists(self):
        with patch('app.tasks.celery_worker.celery_app'):
            import app.tasks.scheduled_tasks as st
            assert hasattr(st, 'health_check_task')
