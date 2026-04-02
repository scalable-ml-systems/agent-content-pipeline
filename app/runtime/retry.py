from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from app.runtime.errors import (
    ProviderStepError,
    RetrievalStepError,
    RuntimeErrorBase,
    TransientStepError,
)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 2
    backoff_seconds: tuple[float, ...] = (1.0, 2.0)
    retryable_exceptions: tuple[Type[Exception], ...] = (
        TransientStepError,
        ProviderStepError,
        RetrievalStepError,
    )

    def should_retry(self, exc: Exception, attempt_number: int) -> bool:
        """
        attempt_number is 1-based.
        """
        if attempt_number >= self.max_attempts:
            return False
        return isinstance(exc, self.retryable_exceptions)

    def backoff_for(self, attempt_number: int) -> float:
        """
        Return sleep duration after a failed attempt.

        If backoff_seconds is shorter than needed, reuse the last value.
        """
        if attempt_number <= 0:
            return 0.0

        index = attempt_number - 1
        if index < len(self.backoff_seconds):
            return self.backoff_seconds[index]

        return self.backoff_seconds[-1] if self.backoff_seconds else 0.0


DEFAULT_RETRY_POLICY = RetryPolicy()