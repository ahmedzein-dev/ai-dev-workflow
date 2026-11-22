"""The engine's single error type."""
from __future__ import annotations


class WorkflowError(Exception):
    """A refused gate or invalid input, reported to the agent; exit code 1 unless set."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code
