"""After a session: persist laps, pit stops and stints from OpenF1, then let Redis expire."""

import uuid
from typing import Any, Protocol

from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import Driver, LapRecord, PitStop, RaceSession, SessionResult, Stint
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from f1_worker.runs import record_run

SOURCE = "openf1"
REDIS_TTL_SECONDS = 6 * 3600


class RecordSource(Protocol):
    async def records(self, endpoint: str, session_key: int) -> list[dict[str, Any]]: ...


def _ms(seconds: Any) -> int | None:
    return None if seconds is None else round(float(seconds) * 1000)


async def _driver_ids(s: AsyncSession, race_id: uuid.UUID) -> dict[int, uuid.UUID]:
    """Car number -> driver. Prefer drivers with a result in this race (numbers get reused
    across eras); fall back to numbers held by exactly one driver."""
    in_race = (
        await s.execute(
            select(Driver.number, Driver.id)
            .join(SessionResult, SessionResult.driver_id == Driver.id)
            .where(SessionResult.race_id == race_id, Driver.number.is_not(None))
            .distinct()
        )
    ).all()
    out: dict[int, uuid.UUID] = {}
    seen: dict[int, int] = {}
    for number, did in (await s.execute(select(Driver.number, Driver.id))).all():
        if number is not None:
            seen[number] = seen.get(number, 0) + 1
            out[number] = did
    out = {n: d for n, d in out.items() if seen[n] == 1}
    out.update({n: d for n, d in in_race if n is not None})
    return out


async def flush_live_session(ctx: dict[str, Any], race_session_id: uuid.UUID) -> int:
    session_factory = ctx["session_factory"]
    source: RecordSource = ctx["openf1"]
    async with record_run(session_factory, "live_flush") as run:
        async with session_factory() as s:
            rs = await s.get(RaceSession, race_session_id)
            if rs is None or rs.openf1_session_key is None:
                return 0
            key = rs.openf1_session_key
            drivers = await _driver_ids(s, rs.race_id)
            written = 0
            for r in await source.records("laps", key):
                did = drivers.get(r.get("driver_number") or -1)
                if did is None or r.get("lap_number") is None:
                    continue
                values: dict[str, Any] = {
                    "lap_time_ms": _ms(r.get("lap_duration")),
                    "s1_ms": _ms(r.get("duration_sector_1")),
                    "s2_ms": _ms(r.get("duration_sector_2")),
                    "s3_ms": _ms(r.get("duration_sector_3")),
                    "is_pit_out": bool(r.get("is_pit_out_lap")),
                }
                await s.execute(
                    insert(LapRecord)
                    .values(
                        id=uuid7(),
                        race_session_id=rs.id,
                        driver_id=did,
                        lap_number=r["lap_number"],
                        source=SOURCE,
                        ingested_at=utcnow(),
                        **values,
                    )
                    .on_conflict_do_update(
                        index_elements=["race_session_id", "driver_id", "lap_number"], set_=values
                    )
                )
                written += 1
            for r in await source.records("pit", key):
                did = drivers.get(r.get("driver_number") or -1)
                if did is None or r.get("lap_number") is None:
                    continue
                values = {"duration_ms": _ms(r.get("pit_duration"))}
                await s.execute(
                    insert(PitStop)
                    .values(
                        id=uuid7(),
                        race_session_id=rs.id,
                        driver_id=did,
                        lap_number=r["lap_number"],
                        source=SOURCE,
                        ingested_at=utcnow(),
                        **values,
                    )
                    .on_conflict_do_update(
                        index_elements=["race_session_id", "driver_id", "lap_number"], set_=values
                    )
                )
                written += 1
            for r in await source.records("stints", key):
                did = drivers.get(r.get("driver_number") or -1)
                if did is None or None in (r.get("stint_number"), r.get("lap_start")):
                    continue
                values = {
                    "compound": r.get("compound") or "UNKNOWN",
                    "lap_start": r["lap_start"],
                    "lap_end": r.get("lap_end"),
                }
                await s.execute(
                    insert(Stint)
                    .values(
                        id=uuid7(),
                        race_session_id=rs.id,
                        driver_id=did,
                        stint_number=r["stint_number"],
                        source=SOURCE,
                        ingested_at=utcnow(),
                        **values,
                    )
                    .on_conflict_do_update(
                        index_elements=["race_session_id", "driver_id", "stint_number"],
                        set_=values,
                    )
                )
                written += 1
            await s.commit()
        base = f"live:{key}"
        for suffix in ("", ":state", ":seq", ":seen", ":cursor"):
            await ctx["redis"].expire(f"{base}{suffix}", REDIS_TTL_SECONDS)
        run.rows = written
        return written
