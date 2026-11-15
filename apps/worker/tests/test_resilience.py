import pytest
from f1_worker.resilience import CircuitBreaker, CircuitOpenError


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def _fail() -> None:
    raise RuntimeError("upstream down")


async def _ok() -> str:
    return "ok"


async def test_opens_after_threshold_and_blocks_calls() -> None:
    cb = CircuitBreaker(failure_threshold=2, reset_seconds=30, clock=Clock())
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_fail)
    with pytest.raises(CircuitOpenError):
        await cb.call(_ok)


async def test_half_open_trial_closes_on_success() -> None:
    clock = Clock()
    cb = CircuitBreaker(failure_threshold=1, reset_seconds=30, clock=clock)
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    clock.now = 31
    assert await cb.call(_ok) == "ok"
    assert await cb.call(_ok) == "ok"


async def test_half_open_trial_failure_reopens() -> None:
    clock = Clock()
    cb = CircuitBreaker(failure_threshold=1, reset_seconds=30, clock=clock)
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    clock.now = 31
    with pytest.raises(RuntimeError):
        await cb.call(_fail)
    with pytest.raises(CircuitOpenError):
        await cb.call(_ok)
