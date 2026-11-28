"""Seed a 2025 calendar, round 1 results and constructor standings from recorded Jolpica
fixtures (deterministic, no network; used by the CI e2e job for the browse pages)."""

import argparse
import asyncio
import json
import os
from pathlib import Path

import httpx
from f1_db.session import make_engine, make_session_factory
from f1_worker.jobs.calendar import ingest_calendar
from f1_worker.jobs.constructors import ingest_constructor_standings
from f1_worker.jobs.results import ingest_results
from f1_worker.sources.jolpica import JolpicaClient

YEAR = 2025
EMPTY: dict[str, object] = {"MRData": {"RaceTable": {"Races": []}}}


def _fixture_client(fixtures: Path) -> JolpicaClient:
    routes = {
        f"/{YEAR}.json": "calendar_2025.json",
        f"/{YEAR}/1/results.json": "race_results_2025_1.json",
        f"/{YEAR}/constructorStandings.json": "constructor_standings_2025.json",
    }

    def handler(req: httpx.Request) -> httpx.Response:
        name = next((f for p, f in routes.items() if req.url.path.endswith(p)), None)
        data = json.loads((fixtures / name).read_text()) if name else EMPTY
        return httpx.Response(200, json=data)

    return JolpicaClient(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args(argv)
    client = _fixture_client(args.fixtures)
    engine = make_engine(os.environ["DATABASE_URL"])
    factory = make_session_factory(engine)
    try:
        count = await ingest_calendar(factory, client, YEAR)
        count += await ingest_results(factory, client, YEAR, 1)
        count += await ingest_constructor_standings(factory, client, YEAR)
    finally:
        await client.client.aclose()
        await engine.dispose()
    print(f"seeded {count} rows for {YEAR}")
    return count


if __name__ == "__main__":
    asyncio.run(main())
