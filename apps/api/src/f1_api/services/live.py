from collections.abc import AsyncIterator

from f1_core.live.codec import dump_state
from f1_core.live.state import TimingState
from redis.asyncio import Redis

WAITING = dump_state(TimingState.empty())
PAGE = 500


class LiveService:
    """Reads what the worker's live poller publishes (see f1_worker.jobs.live_poll).
    Stream entry ids are "<seq>-0", so resuming from a seq is a range read."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    def _stream(self, session_key: int) -> str:
        return f"live:{session_key}"

    async def snapshot(self, session_key: int) -> str:
        raw: str | None = await self.redis.get(f"live:{session_key}:state")
        return raw or WAITING

    async def replay(self, session_key: int, after_seq: int) -> AsyncIterator[tuple[int, str]]:
        start = f"{after_seq + 1}-0"
        while True:
            entries = await self.redis.xrange(self._stream(session_key), min=start, count=PAGE)
            for _, fields in entries:
                yield int(fields["seq"]), fields["state"]
            if len(entries) < PAGE:
                return
            start = "(" + entries[-1][0]

    async def tail(self, session_key: int, after_seq: int, block_ms: int) -> list[tuple[int, str]]:
        res = await self.redis.xread(
            {self._stream(session_key): f"{after_seq}-0"}, block=block_ms, count=100
        )
        return [(int(f["seq"]), f["state"]) for _, items in res for _, f in items]
