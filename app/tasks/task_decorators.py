"""
Task Decorators
Task decorators - Distributed lock implementation
"""
import os
import logging
from functools import wraps
from typing import Callable, Optional
from redis import Redis
from redis.lock import Lock

logger = logging.getLogger(__name__)


def single_instance_task(timeout: int = 3600, blocking: bool = False) -> Callable:
    """
    Single instance task decorator
    Uses Redis distributed lock to ensure only one instance of task executes in distributed environment

    Args:
        timeout: Lock timeout (seconds), prevents deadlock
        blocking: Whether to block waiting for lock

    Usage:
        @celery_app.task
        @single_instance_task(timeout=3600)
        def my_task():
            # This task will only have one instance executing across the entire cluster
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get Redis client
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = Redis.from_url(redis_url, decode_responses=True)

            # Generate lock key (based on function name)
            lock_key = f"celery:lock:{func.__module__}.{func.__name__}"

            # Acquire lock
            lock = redis_client.lock(
                lock_key,
                timeout=timeout,
                blocking=blocking,
                blocking_timeout=5 if blocking else None
            )

            # Attempt to acquire lock
            acquired = lock.acquire(blocking=blocking)

            if not acquired:
                logger.warning(
                    f"Task {func.__name__} is already running in another instance, skipped"
                )
                return {
                    'status': 'skipped',
                    'message': 'Task is already running in another instance'
                }

            try:
                logger.info(f"Task {func.__name__} acquired lock and started execution")
                result = func(*args, **kwargs)
                logger.info(f"Task {func.__name__} completed successfully")
                return result

            except Exception as e:
                logger.error(f"Task {func.__name__} failed with error: {e}")
                raise

            finally:
                # Release lock
                try:
                    lock.release()
                    logger.info(f"Task {func.__name__} released lock")
                except Exception as e:
                    logger.error(f"Failed to release lock for {func.__name__}: {e}")

        return wrapper

    return decorator


def rate_limit_task(
    max_calls: int,
    time_window: int,
    key_prefix: Optional[str] = None
) -> Callable:
    """
    Task rate limit decorator
    Limits task execution frequency within specified time window

    Args:
        max_calls: Maximum number of calls
        time_window: Time window (seconds)
        key_prefix: Redis key prefix (optional)

    Usage:
        @celery_app.task
        @rate_limit_task(max_calls=10, time_window=60)
        def my_task():
            # This task executes maximum 10 times per 60 seconds
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = Redis.from_url(redis_url, decode_responses=True)

            # Generate rate limit key
            prefix = key_prefix or f"celery:ratelimit:{func.__module__}.{func.__name__}"
            rate_key = f"{prefix}:count"

            # Get current count
            current_count = redis_client.get(rate_key)

            if current_count is None:
                # First call, set counter
                redis_client.setex(rate_key, time_window, 1)
                current_count = 1
            else:
                current_count = int(current_count)

                if current_count >= max_calls:
                    logger.warning(
                        f"Task {func.__name__} rate limit exceeded: "
                        f"{current_count}/{max_calls} in {time_window}s"
                    )
                    return {
                        'status': 'rate_limited',
                        'message': f'Rate limit exceeded: {current_count}/{max_calls} in {time_window}s'
                    }

                # Increment count
                redis_client.incr(rate_key)

            # Execute task
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Task {func.__name__} failed: {e}")
                raise

        return wrapper

    return decorator


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: int = 1,
    max_delay: int = 60,
    exponential: bool = True
) -> Callable:
    """
    Retry decorator with exponential backoff

    Args:
        max_retries: Maximum retry count
        base_delay: Base delay (seconds)
        max_delay: Maximum delay (seconds)
        exponential: Whether to use exponential backoff

    Usage:
        @celery_app.task
        @retry_with_backoff(max_retries=3, base_delay=2)
        def my_task():
            # This task automatically retries after failure with exponential delay growth
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                # Calculate retry delay
                retry_count = self.request.retries
                if exponential:
                    delay = min(base_delay * (2 ** retry_count), max_delay)
                else:
                    delay = base_delay

                if retry_count < max_retries:
                    logger.warning(
                        f"Task {func.__name__} failed (attempt {retry_count + 1}/{max_retries}), "
                        f"retrying in {delay}s: {exc}"
                    )
                    raise self.retry(exc=exc, countdown=delay, max_retries=max_retries)
                else:
                    logger.error(
                        f"Task {func.__name__} failed after {max_retries} retries: {exc}"
                    )
                    raise

        return wrapper

    return decorator
