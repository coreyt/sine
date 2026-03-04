"""Async retry utility with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    fn: Any,
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple[type[BaseException], ...] = (OSError,),
    **kwargs: Any,
) -> Any:
    """Retry an async function with exponential backoff and jitter.

    Args:
        fn: Async callable to retry
        *args: Positional arguments forwarded to fn
        max_retries: Maximum number of retry attempts (not counting the initial call)
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay cap in seconds
        retryable_exceptions: Exception types that trigger a retry
        **kwargs: Keyword arguments forwarded to fn

    Returns:
        The return value of fn

    Raises:
        The last exception if all retries are exhausted,
        or any non-retryable exception immediately.
    """
    last_exc: BaseException | None = None

    for attempt in range(1 + max_retries):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = min(base_delay * (2**attempt), max_delay)
                jitter = random.uniform(0, delay)  # noqa: S311
                logger.warning(
                    "Retry %d/%d after error: %s (delay %.1fs)",
                    attempt + 1,
                    max_retries,
                    exc,
                    jitter,
                )
                await asyncio.sleep(jitter)

    raise last_exc  # type: ignore[misc]
