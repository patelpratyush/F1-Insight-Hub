"""Seed driver standings.

Default: ingest the current season live from Jolpica.
`--fixture PATH`: ingest a recorded Jolpica response (deterministic, no network; used by CI).
"""

import argparse
import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from f1_db.session import make_engine, make_session_factory
from f1_worker.jobs.standings import ingest_driver_standings
from f1_worker.sources.jolpica import JolpicaClient


def _fixture_client(path: Path) -> tuple[JolpicaClient, int]:
    data = json.loads(path.read_text())
    year = int(data["MRData"]["StandingsTable"]["season"])
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, json=data))
    return JolpicaClient(client=httpx.AsyncClient(transport=transport)), year


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=datetime.now(UTC).year)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args(argv)
    if args.fixture:
        client, year = _fixture_client(args.fixture)
    else:
        client, year = JolpicaClient(), args.year
    engine = make_engine(os.environ["DATABASE_URL"])
    try:
        count = await ingest_driver_standings(make_session_factory(engine), client, year)
    finally:
        await client.client.aclose()
        await engine.dispose()
    print(f"seeded {count} rows for {year}")
    return count


if __name__ == "__main__":
    asyncio.run(main())
