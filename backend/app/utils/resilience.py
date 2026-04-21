import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Type


logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base exception with a retryability category."""

    reason_code = "pipeline_error"
    retryable = False


class RetryablePipelineError(PipelineError):
    reason_code = "retryable_error"
    retryable = True


class PermanentPipelineError(PipelineError):
    reason_code = "permanent_error"
    retryable = False


class RateLimitedPipelineError(RetryablePipelineError):
    reason_code = "rate_limited"


@dataclass
class RetryStats:
    attempts: int = 0
    failures: int = 0
    exhausted: bool = False
    last_error: Optional[str] = None


def retry_call(
    fn: Callable[[], Any],
    *,
    operation: str,
    max_retries: int = 3,
    backoff_base_seconds: float = 0.5,
    retriable_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Tuple[Any, RetryStats]:
    """Execute callable with retry/backoff, returning result + retry stats."""
    stats = RetryStats()
    for attempt in range(1, max_retries + 1):
        stats.attempts = attempt
        try:
            return fn(), stats
        except retriable_exceptions as exc:
            stats.failures += 1
            stats.last_error = str(exc)
            is_last_attempt = attempt >= max_retries
            logger.warning(
                "operation_failed operation=%s attempt=%s/%s error=%s",
                operation,
                attempt,
                max_retries,
                exc,
            )
            if is_last_attempt:
                stats.exhausted = True
                raise
            sleep_seconds = backoff_base_seconds * (2 ** (attempt - 1))
            time.sleep(sleep_seconds)

    stats.exhausted = True
    raise RuntimeError(f"Retry loop for {operation} exited unexpectedly")


def classify_exception(exc: BaseException) -> str:
    if isinstance(exc, RateLimitedPipelineError):
        return "rate_limited"
    if isinstance(exc, RetryablePipelineError):
        return "retryable"
    if isinstance(exc, PermanentPipelineError):
        return "permanent"
    return "unknown"

