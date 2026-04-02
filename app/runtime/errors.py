from __future__ import annotations


class RuntimeErrorBase(Exception):
    """Base class for all runtime-controlled failures."""


class TransientStepError(RuntimeErrorBase):
    """
    Retryable failure.

    Use for temporary network/provider/timeouts or flaky upstream calls.
    """


class ProviderStepError(TransientStepError):
    """Retryable failure from an LLM or external provider."""


class RetrievalStepError(TransientStepError):
    """Retryable failure in retrieval/index lookup."""


class ValidationStepError(RuntimeErrorBase):
    """
    Non-retryable logical validation failure unless explicitly configured.

    Example:
    - unsupported claims
    - missing required evidence
    - style drift beyond threshold
    """


class TerminalStepError(RuntimeErrorBase):
    """
    Immediate stop.

    Use when continuing would be incorrect.
    """


class StateContractError(RuntimeErrorBase):
    """
    Runtime/state contract violation.

    This usually indicates a programming error, not a recoverable condition.
    """