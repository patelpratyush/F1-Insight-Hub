"""Live SSE fan-out and lag check (plain asyncio, no k6).

    uv run python apps/api/tests/load/live_fanout.py [--clients 300] [--seconds 60]
        [--redis-url redis://localhost:6379/0]   (or REDIS_URL)

Starts the api with uvicorn on a free port, opens N SSE clients on /v1/live/990001/stream,
then XADDs one stream entry per second (the shape the worker's poller writes) whose state
carries an extra leading `published_at` epoch timestamp. The api forwards the state verbatim,
so each client measures publish-to-receive latency. Prints `p95=...ms` and exits 1 if
p95 >= 1000 ms or any client missed an entry.

The api runs in its own uvicorn process (as in production): sharing one event loop with 300
client readers measures this harness, not the api (p95 1.4 s in-process vs 0.2 s separate on
a 2019 laptop). Needs no Postgres: the api's engine connects lazily and SSE never uses it.

Per-IP limit: the api allows 3 streams per client IP (`live:conn:<ip>`, IP from client_ip()).
All clients here come from 127.0.0.1, so the api is started with TRUSTED_PROXY_HOPS=1 and each
client sends its own X-Forwarded-For, so each looks like a different viewer behind one proxy
(as on Railway). Production code and limits are unchanged; 300 clients stay under the
500-per-instance cap.
"""

import argparse
import asyncio
import json
import os
import resource
import socket
import statistics
import sys
import time

import httpx
from f1_core.live.codec import state_dict
from f1_core.live.state import DriverTiming, TimingState
from redis.asyncio import Redis

KEY = 990001  # no real OpenF1 session uses this
BUDGET_MS = 1000.0
STAMP = '{"published_at":'


def _entry_state(seq: int) -> str:
    drivers = {n: DriverTiming(number=n, position=i + 1) for i, n in enumerate(range(1, 21))}
    body = state_dict(TimingState(drivers=drivers, last_seq=seq, status="live"))
    return json.dumps({"published_at": time.time(), **body})  # first key: cheap to read back


async def _client(
    http: httpx.AsyncClient,
    ip: str,
    on_ready: asyncio.Queue[None],
    latencies: list[float],
    received: list[int],
    i: int,
) -> None:
    headers = {"X-Forwarded-For": ip}
    async with http.stream("GET", f"/v1/live/{KEY}/stream", headers=headers) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            data = line[5:].lstrip()
            if not data.startswith(STAMP):  # initial "waiting" snapshot
                on_ready.put_nowait(None)
                continue
            # Not json.loads: parsing 300 full states would measure this harness, not the api.
            sent_at = float(data[len(STAMP) : data.index(",")])
            latencies.append((time.time() - sent_at) * 1000)
            received[i] += 1


async def _start_api(redis_url: str) -> tuple[asyncio.subprocess.Process, str]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "REDIS_URL": redis_url, "TRUSTED_PROXY_HOPS": "1", "ENVIRONMENT": "test"}
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "uvicorn",
        "f1_api.main:create_app",
        "--factory",
        "--port",
        str(port),
        "--no-access-log",
        "--log-level",
        "warning",
        env=env,
    )
    base = f"http://127.0.0.1:{port}"
    async with httpx.AsyncClient(base_url=base) as http, asyncio.timeout(30):
        while True:
            try:
                (await http.get(f"/v1/live/{KEY}/snapshot")).raise_for_status()
                return proc, base
            except httpx.TransportError:
                await asyncio.sleep(0.2)


async def run(redis_url: str, clients: int, seconds: int) -> int:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.delete(f"live:{KEY}", f"live:{KEY}:state")
    proc, base = await _start_api(redis_url)
    latencies: list[float] = []
    received = [0] * clients
    on_ready: asyncio.Queue[None] = asyncio.Queue()
    limits = httpx.Limits(max_connections=clients + 10)
    timeout = httpx.Timeout(10.0, read=None)
    try:
        async with httpx.AsyncClient(base_url=base, limits=limits, timeout=timeout) as http:
            ips = [f"10.9.{i // 250}.{i % 250 + 1}" for i in range(clients)]
            tasks = [
                asyncio.create_task(_client(http, ip, on_ready, latencies, received, i))
                for i, ip in enumerate(ips)
            ]
            async with asyncio.timeout(30):
                for _ in range(clients):
                    await on_ready.get()
            print(f"{clients} clients connected; publishing for {seconds}s", flush=True)
            for seq in range(1, seconds + 1):
                await redis.xadd(
                    f"live:{KEY}",
                    {"seq": seq, "payload": "[]", "state": _entry_state(seq)},
                    id=f"{seq}-0",
                )
                await asyncio.sleep(1)
            await asyncio.sleep(2)  # let the last entry land
            for t in tasks:
                t.cancel()
            results = await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        proc.terminate()
        await proc.wait()
        await redis.delete(f"live:{KEY}", f"live:{KEY}:state")
        await redis.aclose()

    failed = [r for r in results if isinstance(r, Exception)]  # CancelledError is not one
    missed = sum(seconds - r for r in received)
    p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) > 1 else float("inf")
    print(
        f"p95={p95:.1f}ms p50={statistics.median(latencies or [0]):.1f}ms "
        f"max={max(latencies or [0]):.1f}ms clients={clients} seconds={seconds} "
        f"received={len(latencies)} missed={missed} client_errors={len(failed)}",
        flush=True,
    )
    return 0 if p95 < BUDGET_MS and missed == 0 and not failed else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clients", type=int, default=300)
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument(
        "--redis-url", default=os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    )
    args = parser.parse_args()
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)  # macOS default soft limit is 256
    want = 4 * args.clients + 256
    if soft < want:
        resource.setrlimit(resource.RLIMIT_NOFILE, (min(want, hard), hard))
    sys.exit(asyncio.run(run(args.redis_url, args.clients, args.seconds)))


if __name__ == "__main__":
    main()
