"""
Task Decorators Unit Tests
Tests for app/tasks/task_decorators.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from functools import wraps


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator"""

    def test_retry_decorator_wraps_function(self):
        """Decorator preserves function name and docstring"""
        from app.tasks.task_decorators import retry_with_backoff

        @retry_with_backoff(max_retries=3, base_delay=1)
        def my_task(self, x, y):
            """My task doc"""
            return x + y

        assert my_task.__name__ == 'my_task'
        assert 'My task doc' in (my_task.__doc__ or '')

    def test_retry_success_on_first_try(self):
        """Task succeeds without retry"""
        from app.tasks.task_decorators import retry_with_backoff

        @retry_with_backoff(max_retries=3, base_delay=1)
        def my_task(self):
            return 'success'

        mock_self = Mock()
        mock_self.request.retries = 0
        result = my_task(mock_self)
        assert result == 'success'

    def test_retry_raises_after_max_retries(self):
        """Task raises after max retries exceeded"""
        from app.tasks.task_decorators import retry_with_backoff

        @retry_with_backoff(max_retries=2, base_delay=1)
        def failing_task(self):
            raise ValueError("I always fail")

        mock_self = Mock()
        mock_self.request.retries = 2  # Already at max
        mock_self.retry.side_effect = Exception("Should not retry")

        with pytest.raises(ValueError, match="I always fail"):
            failing_task(mock_self)

    def test_retry_calls_self_retry_when_under_max(self):
        """Task calls self.retry() when under max retries"""
        from app.tasks.task_decorators import retry_with_backoff

        @retry_with_backoff(max_retries=3, base_delay=2)
        def flaky_task(self):
            raise ConnectionError("Network error")

        mock_self = Mock()
        mock_self.request.retries = 0

        class SentinelError(Exception):
            pass

        mock_self.retry.side_effect = SentinelError("retrying")

        with pytest.raises(SentinelError):
            flaky_task(mock_self)

        mock_self.retry.assert_called_once()
        call_kwargs = mock_self.retry.call_args
        assert 'countdown' in call_kwargs.kwargs or len(call_kwargs.args) > 0

    def test_exponential_backoff_calculation(self):
        """Verify exponential backoff formula"""
        from app.tasks.task_decorators import retry_with_backoff

        delays_used = []

        @retry_with_backoff(max_retries=5, base_delay=2, max_delay=60, exponential=True)
        def tracking_task(self):
            raise RuntimeError("fail")

        for retry_num in range(3):
            mock_self = Mock()
            mock_self.request.retries = retry_num

            class SentinelError(Exception):
                pass

            mock_self.retry.side_effect = SentinelError()
            try:
                tracking_task(mock_self)
            except SentinelError:
                pass
            if mock_self.retry.called:
                call_kwargs = mock_self.retry.call_args.kwargs
                delays_used.append(call_kwargs.get('countdown', None))

        # Delays should be 2, 4, 8 (exponential)
        assert delays_used[0] == 2
        assert delays_used[1] == 4
        assert delays_used[2] == 8

    def test_linear_backoff_when_exponential_false(self):
        """Verify linear backoff when exponential=False"""
        from app.tasks.task_decorators import retry_with_backoff

        @retry_with_backoff(max_retries=5, base_delay=3, exponential=False)
        def linear_task(self):
            raise RuntimeError("fail")

        mock_self = Mock()
        mock_self.request.retries = 1

        class SentinelError(Exception):
            pass

        mock_self.retry.side_effect = SentinelError()
        try:
            linear_task(mock_self)
        except SentinelError:
            pass

        call_kwargs = mock_self.retry.call_args.kwargs
        assert call_kwargs.get('countdown') == 3  # Always base_delay

    def test_max_delay_cap(self):
        """Backoff should not exceed max_delay"""
        from app.tasks.task_decorators import retry_with_backoff

        @retry_with_backoff(max_retries=10, base_delay=2, max_delay=10, exponential=True)
        def capped_task(self):
            raise RuntimeError("fail")

        mock_self = Mock()
        mock_self.request.retries = 5  # 2^5 * 2 = 64, capped to 10

        class SentinelError(Exception):
            pass

        mock_self.retry.side_effect = SentinelError()
        try:
            capped_task(mock_self)
        except SentinelError:
            pass

        call_kwargs = mock_self.retry.call_args.kwargs
        assert call_kwargs.get('countdown') == 10


class TestSingleInstanceTask:
    """Tests for single_instance_task decorator (mocked Redis)"""

    @patch('app.tasks.task_decorators.Redis')
    def test_executes_when_lock_acquired(self, MockRedis):
        from app.tasks.task_decorators import single_instance_task

        mock_redis = Mock()
        mock_lock = Mock()
        mock_lock.acquire.return_value = True
        mock_redis.lock.return_value = mock_lock
        MockRedis.from_url.return_value = mock_redis

        @single_instance_task(timeout=60)
        def my_task():
            return 'done'

        result = my_task()
        assert result == 'done'
        mock_lock.release.assert_called_once()

    @patch('app.tasks.task_decorators.Redis')
    def test_skipped_when_lock_not_acquired(self, MockRedis):
        from app.tasks.task_decorators import single_instance_task

        mock_redis = Mock()
        mock_lock = Mock()
        mock_lock.acquire.return_value = False
        mock_redis.lock.return_value = mock_lock
        MockRedis.from_url.return_value = mock_redis

        @single_instance_task(timeout=60)
        def busy_task():
            return 'should not run'

        result = busy_task()
        assert result['status'] == 'skipped'

    @patch('app.tasks.task_decorators.Redis')
    def test_lock_released_on_exception(self, MockRedis):
        from app.tasks.task_decorators import single_instance_task

        mock_redis = Mock()
        mock_lock = Mock()
        mock_lock.acquire.return_value = True
        mock_redis.lock.return_value = mock_lock
        MockRedis.from_url.return_value = mock_redis

        @single_instance_task(timeout=60)
        def failing_task():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            failing_task()

        mock_lock.release.assert_called_once()


class TestRateLimitTask:
    """Tests for rate_limit_task decorator (mocked Redis)"""

    @patch('app.tasks.task_decorators.Redis')
    def test_executes_within_limit(self, MockRedis):
        from app.tasks.task_decorators import rate_limit_task

        mock_redis = Mock()
        mock_redis.get.return_value = None  # First call
        MockRedis.from_url.return_value = mock_redis

        @rate_limit_task(max_calls=10, time_window=60)
        def limited_task():
            return 'ok'

        result = limited_task()
        assert result == 'ok'
        mock_redis.setex.assert_called_once()

    @patch('app.tasks.task_decorators.Redis')
    def test_rate_limited_when_over_limit(self, MockRedis):
        from app.tasks.task_decorators import rate_limit_task

        mock_redis = Mock()
        mock_redis.get.return_value = b'10'  # At limit
        MockRedis.from_url.return_value = mock_redis

        @rate_limit_task(max_calls=10, time_window=60)
        def limited_task():
            return 'ok'

        result = limited_task()
        assert result['status'] == 'rate_limited'

    @patch('app.tasks.task_decorators.Redis')
    def test_increments_counter_under_limit(self, MockRedis):
        from app.tasks.task_decorators import rate_limit_task

        mock_redis = Mock()
        mock_redis.get.return_value = b'5'  # Under limit
        MockRedis.from_url.return_value = mock_redis

        @rate_limit_task(max_calls=10, time_window=60)
        def limited_task():
            return 'run'

        result = limited_task()
        assert result == 'run'
        mock_redis.incr.assert_called_once()
