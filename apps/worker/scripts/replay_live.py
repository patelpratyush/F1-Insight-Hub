"""Dev-only: replay recorded live events into Redis so a session can be shown without a race.

    uv run python apps/worker/scripts/replay_live.py FIXTURE.jsonl --speed 5 \
        [--session-key 9999] [--redis-url redis://localhost:6379/0]

FIXTURE is JSON Lines, one of:
  {"ts": ISO, "kind": ..., "driver_number": int|null, "data": {...}}   a LiveEvent minus seq
  {"pause_s": 25}   publish nothing for 25 wall-clock seconds (NOT divided by --speed),
                    then continue with the next event straight away

Events are published in recorded time divided by --speed; events due within the same tick
go out as one batch through the real poller (`poll_once`), so the stream entries and state
are exactly what production writes. Existing `live:<key>*` keys are deleted first, so
re-running starts a clean session.
"""

import argparse
import asyncio
import json
import os
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from pathlib import Path

from f1_core.live.events import LiveEvent
from f1_worker.jobs.live_poll import poll_once
from redis.asyncio import Redis

TICK_S = 0.25  # wall seconds; events due within one tick share a stream entry
SUFFIXES = ("", ":state", ":seq", ":seen", ":cursor")

Item = LiveEvent | float  # float = pause in wall seconds


def read_fixture(path: Path) -> list[Item]:
    items: list[Item] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "pause_s" in row:
            items.append(float(row["pause_s"]))
        else:
            items.append(
                LiveEvent(
                    seq=0,
                    ts=datetime.fromisoformat(row["ts"]),
                    kind=row["kind"],
                    driver_number=row["driver_number"],
                    data=row["data"],
                )
            )
    return items


class _Batch:
    """A LiveSource that hands the poller whatever batch is queued."""

    def __init__(self) -> None:
        self.events: list[LiveEvent] = []

    async def events_since(
        self, session_key: int, after: Mapping[str, datetime] | None
    ) -> list[LiveEvent]:
        out, self.events = self.events, []
        return out


async def replay(
    redis: Redis,
    items: list[Item],
    session_key: int,
    speed: float,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> int:
    """Publish `items` into live:<session_key>. Returns the number of events published."""
    await redis.delete(*(f"live:{session_key}{s}" for s in SUFFIXES))
    source = _Batch()
    published = 0
    elapsed = 0.0  # wall seconds slept so far
    base_ts: datetime | None = None  # recorded time that maps to base_elapsed
    base_elapsed = 0.0
    batch_due = 0.0

    async def flush() -> None:
        nonlocal published
        if source.events:
            published += await poll_once(redis, source, session_key)
            print(f"published seq={published} at +{elapsed:.1f}s", flush=True)

    for item in items:
        if isinstance(item, float):
            await flush()
            print(f"pause {item:g}s", flush=True)
            await sleep(item)
            elapsed += item
            base_ts = None  # the pause replaces the recorded gap
            continue
        if base_ts is None:
            base_ts, base_elapsed = item.ts, elapsed
        due = base_elapsed + (item.ts - base_ts).total_seconds() / speed
        if source.events and due - batch_due >= TICK_S:
            await flush()
        if not source.events:
            if due > elapsed:
                await sleep(due - elapsed)
                elapsed = due
            batch_due = due
        source.events.append(item)
    await flush()
    return published


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--session-key", type=int, default=9999)
    parser.add_argument(
        "--redis-url", default=os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    )
    args = parser.parse_args(argv)
    redis = Redis.from_url(args.redis_url)
    try:
        count = await replay(redis, read_fixture(args.fixture), args.session_key, args.speed)
    finally:
        await redis.aclose()
    print(f"done: {count} events into live:{args.session_key}", flush=True)
    return count


if __name__ == "__main__":
    asyncio.run(main())
