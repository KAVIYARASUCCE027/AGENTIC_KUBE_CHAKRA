"""
Retry Service Module — Phase 3.

Provides a production-grade retry decorator with exponential backoff,
configurable max attempts, and jitter.  Designed for wrapping unreliable
I/O calls (Spring Boot REST, network, cache) without leaking retry
logic into business code.

Features:
    • Exponential backoff with optional jitter to avoid thundering-herd.
    • Per-attempt structured logging (attempt number, delay, exception).
    • Configurable exception allow-list so only transient failures retry.
    • Raises the **last** exception unchanged when retries are exhausted.

Usage:
    >>> from services.retry_service import with_retry
    >>>
    >>> @with_retry(max_retries=3, base_delay=1.0)
    ... def fetch_data():
    ...     return requests.get(url, timeout=5).json()
"""

from __future__ import annotations

import logging
import random
import time
import asyncio
from functools import wraps
from typing import Any, Callable, Sequence, Type

logger = logging.getLogger(__name__)

from schemas.event_message import EventMessage
from memory.dead_letter_queue import DeadLetterQueue

class EventRetryService:
    """
    Retry logic for event bus handlers.
    After max_retries, pushes the failed event to the Dead Letter Queue.
    """
    def __init__(self, dlq: DeadLetterQueue, max_retries: int = 3, base_delay: float = 2.0, backoff_factor: float = 2.0):
        self.dlq = dlq
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor

    async def execute_with_retry(self, handler: Callable, event: EventMessage) -> bool:
        """
        Executes a handler with exponential backoff.
        Returns True if successful, False if sent to DLQ.
        """
        delay = self.base_delay
        for attempt in range(1, self.max_retries + 2):
            try:
                await handler(event)
                return True
            except Exception as e:
                if attempt > self.max_retries:
                    logger.error(f"Event {event.event_id} failed after {self.max_retries} retries: {e}. Sending to DLQ.")
                    self.dlq.add(event, str(e))
                    return False
                
                logger.warning(f"Handler failed for event {event.event_id} (Attempt {attempt}/{self.max_retries}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= self.backoff_factor
        return False


# Default transient exceptions that warrant a retry
_DEFAULT_RETRYABLE: tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Sequence[Type[Exception]] | None = None,
) -> Callable:
    """
    Decorator factory that wraps a function with retry-on-failure logic.

    Args:
        max_retries:
            Maximum number of retry attempts **after** the first call.
            Total attempts = 1 + max_retries.
        base_delay:
            Initial delay in seconds before the first retry.
        max_delay:
            Upper bound on the delay between retries (caps exponential growth).
        backoff_factor:
            Multiplier applied to the delay after each retry.
        jitter:
            If ``True``, adds ±25 % random jitter to each delay to prevent
            thundering-herd effects across concurrent callers.
        retryable_exceptions:
            Exception types that should trigger a retry.  Defaults to
            ``(ConnectionError, TimeoutError, OSError)``.

    Returns:
        A decorator that applies retry logic to the wrapped function.

    Raises:
        The last exception raised by the wrapped function after all
        retries have been exhausted.
    """
    retry_on: tuple[Type[Exception], ...] = (
        tuple(retryable_exceptions) if retryable_exceptions else _DEFAULT_RETRYABLE
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            delay = base_delay

            for attempt in range(1, max_retries + 2):  # 1-indexed, +1 for initial try
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    last_exception = exc

                    if attempt > max_retries:
                        logger.error(
                            "Retry exhausted for '%s' after %d attempts. "
                            "Last error: %s",
                            func.__name__,
                            attempt,
                            exc,
                        )
                        raise

                    # Calculate sleep with optional jitter
                    sleep_time = min(delay, max_delay)
                    if jitter:
                        sleep_time *= 1.0 + random.uniform(-0.25, 0.25)

                    logger.warning(
                        "Attempt %d/%d for '%s' failed: %s — "
                        "retrying in %.2fs…",
                        attempt,
                        max_retries + 1,
                        func.__name__,
                        exc,
                        sleep_time,
                    )

                    time.sleep(sleep_time)
                    delay *= backoff_factor

            # Should never reach here, but satisfy type checkers
            if last_exception is not None:
                raise last_exception  # pragma: no cover

        return wrapper
    return decorator
