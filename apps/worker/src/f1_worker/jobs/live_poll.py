"""Poll OpenF1 for one session and publish reduced timing state to Redis.

Keys (all expire after 24 h):
  live:{key}         stream; one entry per poll that produced events, entry id = "<last seq>-0",
                     fields: seq, payload (JSON list of events), state (TimingState JSON)
  live:{key}:state   latest TimingState JSON (snapshot)
  live:{key}:seq     INCR counter for event seq
  live:{key}:seen    dedupe set of event fingerprints
  live:{key}:cursor  hash kind -> latest ISO timestamp fetched (per-endpoint `after`)
"""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Protocol, cast

import structlog
from f1_core.live.codec import dump_state, load_state
from f1_core.live.events import LiveEvent
from f1_core.live.reducer import apply_event
from f1_core.live.state import TimingState
from f1_db.models import RaceSession
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from f1_worker.sources.openf1 import ENDPOINTS, OpenF1Unavailable

STREAM_MAXLEN = 20_000
KEY_TTL_SECONDS = 24 * 3600
DATED_KINDS = {kind for kind, date_field in ENDPOINTS.values() if date_field}

log = structlog.get_logger()


class LiveSource(Protocol):
    async def events_since(
        self, session_key: int, after: Mapping[str, datetime] | None
    ) -> list[LiveEvent]: ...


def _s(v: bytes | str) -> str:
    return v.decode() if isinstance(v, bytes) else v


def _fingerprint(e: LiveEvent) -> str:
    raw = json.dumps([e.kind, e.driver_number, e.ts.isoformat(), e.data], sort_keys=True)
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()


def _event_json(e: LiveEvent) -> dict[str, Any]:
    return {
        "seq": e.seq,
        "ts": e.ts.isoformat(),
        "kind": e.kind,
        "driver_number": e.driver_number,
        "data": dict(e.data),
    }


async def poll_once(redis: Redis, client: LiveSource, session_key: int) -> int:
    """One poll. Returns the number of events published (0 when nothing changed)."""
    base = f"live:{session_key}"
    raw_state = await redis.get(f"{base}:state")
    state = load_state(raw_state) if raw_state else TimingState.empty()
    # redis-py types hash commands as `Awaitable | value` (shared sync/async stubs).
    raw_cursors = await cast(
        Awaitable[dict[bytes | str, bytes | str]], redis.hgetall(f"{base}:cursor")
    )
    cursors = {_s(k): datetime.fromisoformat(_s(v)) for k, v in raw_cursors.items()}

    new: list[LiveEvent] = []
    try:
        events = await client.events_since(session_key, cursors)
    except OpenF1Unavailable as exc:
        log.warning("openf1_unavailable", session_key=session_key, error=str(exc))
        events = []
        if state.status == "live":  # tell viewers the feed stopped; UI shows "Waiting"
            new = [_status_event(state, "waiting")]
    else:
        if events:
            pipe = redis.pipeline(transaction=False)
            for e in events:
                pipe.sadd(f"{base}:seen", _fingerprint(e))
            added = await pipe.execute()
            new = [e for e, was_new in zip(events, added, strict=True) if was_new]
        if new and state.status != "live":
            new.insert(0, _status_event(state, "live", ts=new[0].ts))
    for e in events:
        if e.kind in DATED_KINDS and (e.kind not in cursors or e.ts > cursors[e.kind]):
            cursors[e.kind] = e.ts

    cursor_map = {k: v.isoformat() for k, v in cursors.items()}
    if not new:
        if cursor_map:
            await cast(Awaitable[int], redis.hset(f"{base}:cursor", mapping=cursor_map))
        return 0

    last = await redis.incrby(f"{base}:seq", len(new))
    numbered = [replace(e, seq=last - len(new) + 1 + i) for i, e in enumerate(new)]
    for e in numbered:
        state = apply_event(state, e)
    state_json = dump_state(state)

    pipe = redis.pipeline(transaction=True)  # snapshot and stream stay consistent
    pipe.xadd(
        base,
        {
            "seq": last,
            "payload": json.dumps([_event_json(e) for e in numbered]),
            "state": state_json,
        },
        id=f"{last}-0",
        maxlen=STREAM_MAXLEN,
        approximate=True,
    )
    pipe.set(f"{base}:state", state_json)
    if cursor_map:
        pipe.hset(f"{base}:cursor", mapping=cursor_map)
    for suffix in ("", ":state", ":seq", ":seen", ":cursor"):
        pipe.expire(f"{base}{suffix}", KEY_TTL_SECONDS)
    await pipe.execute()
    return len(numbered)


def _status_event(state: TimingState, status: str, ts: datetime | None = None) -> LiveEvent:
    return LiveEvent(
        seq=0,
        ts=ts or datetime.now(UTC),
        kind="status",
        driver_number=None,
        data={"session": status},
    )


async def _is_live(session_factory: async_sessionmaker[AsyncSession], session_key: int) -> bool:
    async with session_factory() as s:
        status = (
            await s.execute(
                select(RaceSession.status).where(RaceSession.openf1_session_key == session_key)
            )
        ).scalar_one_or_none()
    return status == "live"


async def poll_live_session(ctx: dict[str, Any], session_key: int) -> int:
    """Poll while the session is live. Returns total events published."""
    total = 0
    interval: float = ctx.get("openf1_poll_seconds", 15.0)
    while await _is_live(ctx["session_factory"], session_key):
        total += await poll_once(ctx["redis"], ctx["openf1"], session_key)
        await asyncio.sleep(interval)
    return total
