"""Live timing: snapshot and SSE stream. Data is unofficial, community data (OpenF1)."""

import json
from collections.abc import AsyncIterator

import anyio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sse_starlette import EventSourceResponse, ServerSentEvent

from f1_api.deps import RedisDep
from f1_api.errors import ProblemError
from f1_api.middleware.rate_limit import client_ip, rate_limit
from f1_api.schemas.live import LiveStateOut
from f1_api.services.live import LiveService

router = APIRouter(prefix="/v1/live", tags=["live"])

HEARTBEAT_SECONDS = 15.0
MAX_PER_IP = 3  # across api instances (Redis)
MAX_PER_INSTANCE = 500  # this process
SLOT_TTL_SECONDS = 60  # refreshed while streaming; a crashed instance's slots expire


@router.get(
    "/{session_key}/snapshot",
    response_model=LiveStateOut,
    dependencies=[Depends(rate_limit(120, 60))],
    operation_id="getLiveSnapshot",
)
async def snapshot(session_key: int, redis: RedisDep) -> JSONResponse:
    raw = await LiveService(redis).snapshot(session_key)
    return JSONResponse(json.loads(raw), headers={"Cache-Control": "no-store"})


async def _acquire(request: Request, redis: Redis, ip_key: str) -> bool:
    state = request.app.state
    if getattr(state, "live_streams", 0) >= MAX_PER_INSTANCE:
        return False
    pipe = redis.pipeline(transaction=True)
    pipe.incr(ip_key)
    pipe.expire(ip_key, SLOT_TTL_SECONDS)
    count, _ = await pipe.execute()
    if count > MAX_PER_IP:
        await redis.decr(ip_key)
        return False
    state.live_streams = getattr(state, "live_streams", 0) + 1
    return True


async def _release(request: Request, redis: Redis, ip_key: str) -> None:
    request.app.state.live_streams -= 1
    if await redis.decr(ip_key) <= 0:
        await redis.delete(ip_key)


@router.get(
    "/{session_key}/stream",
    responses={200: {"content": {"text/event-stream": {}}}, 429: {"description": "Too many"}},
    operation_id="streamLive",
)
async def stream(session_key: int, request: Request, redis: RedisDep) -> EventSourceResponse:
    ip_key = f"live:conn:{client_ip(request)}"
    if not await _acquire(request, redis, ip_key):
        raise ProblemError(429, "Too many streams", "Close another live tab and retry")
    try:
        last_id = int(request.headers.get("last-event-id") or 0)
    except ValueError:
        last_id = 0
    service = LiveService(redis)

    async def gen() -> AsyncIterator[ServerSentEvent]:
        try:
            sent = last_id
            if last_id > 0:  # resume: every entry after the client's last seq, in order
                async for seq, state in service.replay(session_key, last_id):
                    sent = seq
                    yield ServerSentEvent(data=state, event="tower", id=str(seq))
            if sent == last_id:  # fresh client, or nothing to replay: current snapshot
                snap = await service.snapshot(session_key)
                snap_seq = int(json.loads(snap)["last_seq"])
                if snap_seq == 0:
                    yield ServerSentEvent(data=snap, event="tower")  # status: waiting
                elif snap_seq > sent:
                    sent = snap_seq
                    yield ServerSentEvent(data=snap, event="tower", id=str(snap_seq))
            while True:
                await redis.expire(ip_key, SLOT_TTL_SECONDS)
                entries = await service.tail(session_key, sent, int(HEARTBEAT_SECONDS * 1000))
                if not entries:
                    yield ServerSentEvent(comment="heartbeat")
                for seq, state in entries:
                    if seq > sent:
                        sent = seq
                        yield ServerSentEvent(data=state, event="tower", id=str(seq))
        finally:
            with anyio.CancelScope(shield=True):  # runs even when the client disconnects
                await _release(request, redis, ip_key)

    return EventSourceResponse(
        gen(),
        ping=None,  # we send our own heartbeat comments
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
