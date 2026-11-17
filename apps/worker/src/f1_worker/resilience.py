import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int,
        reset_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self.clock = clock
        self.failures = 0
        self.opened_at: float | None = None

    def _allow(self) -> bool:
        if self.opened_at is None:
            return True
        # half-open: allow one trial after reset_seconds
        return self.clock() - self.opened_at >= self.reset_seconds

    async def call(self, fn: Callable[[], Awaitable[T]]) -> T:
        if not self._allow():
            raise CircuitOpenError("circuit open")
        try:
            result = await fn()
        except Exception:
            self.failures += 1
            if self.opened_at is not None or self.failures >= self.failure_threshold:
                self.opened_at = self.clock()
            raise
        self.failures = 0
        self.opened_at = None
        return result
