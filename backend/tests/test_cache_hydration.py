import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone

import aiosqlite

from app.services.cache import CacheService


async def _make_db_with_entries(db_path: str, entries: dict):
    """entries: {key: (data, ttl)}"""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "CREATE TABLE cache_entries (key TEXT PRIMARY KEY, data TEXT, fetched_at TEXT, ttl INTEGER)"
        )
        now = datetime.now(timezone.utc).isoformat()
        for key, (data, ttl) in entries.items():
            await db.execute(
                "INSERT INTO cache_entries VALUES (?,?,?,?)",
                (key, json.dumps(data), now, ttl),
            )
        await db.commit()


class _StubJolpica:
    async def get_schedule(self, year): return []
    async def get_drivers(self, year): return []
    async def get_constructors(self, year): return []
    async def get_driver_standings(self, year): return []
    async def get_constructor_standings(self, year): return []


class TestHydrationYearLoadedGuard:
    def test_permanent_subresource_alone_does_not_mark_year_loaded(self):
        """A cached race_result (TTL_PERMANENT) for a year must not, by
        itself, cause ensure_year() to treat that year's standings as
        already loaded -- this was a real bug: driver_standings has a 5min
        TTL and expires long before a permanent race_result key does, so
        after a restart the year looked "loaded" while standings were empty."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test_cache.db")

            async def run():
                await _make_db_with_entries(db_path, {
                    "race_result:2024:1": ({"raceName": "Test GP"}, 0),  # TTL_PERMANENT
                })
                cache = CacheService(db_path=db_path, jolpica=_StubJolpica())
                await cache.open()
                await cache._hydrate()
                assert 2024 not in cache._loaded_years
                await cache.close()

            asyncio.run(run())

    def test_year_with_standings_present_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test_cache.db")

            async def run():
                await _make_db_with_entries(db_path, {
                    "driver_standings:2024": ([{"driver": "VER"}], 300),
                    "schedule:2024": ([], 86400),
                })
                cache = CacheService(db_path=db_path, jolpica=_StubJolpica())
                await cache.open()
                await cache._hydrate()
                assert 2024 in cache._loaded_years
                await cache.close()

            asyncio.run(run())

    def test_schedule_without_standings_does_not_mark_year_loaded(self):
        """schedule/drivers have a 24h TTL vs standings' 5min -- if only the
        long-lived key survived hydration, the year must still be treated as
        not-loaded so ensure_year() refetches standings."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test_cache.db")

            async def run():
                await _make_db_with_entries(db_path, {
                    "schedule:2024": ([], 86400),
                })
                cache = CacheService(db_path=db_path, jolpica=_StubJolpica())
                await cache.open()
                await cache._hydrate()
                assert 2024 not in cache._loaded_years
                await cache.close()

            asyncio.run(run())
