"""Race-session lifecycle: scheduled -> live -> finished, and when to poll OpenF1."""

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any, Protocol

import structlog
from f1_db.models import Race, RaceSession, Season, SessionResult
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

LIVE_LEAD = timedelta(minutes=5)  # live from starts_at - 5 min
MAX_DURATION = timedelta(hours=3)  # finished at starts_at + 3 h if OpenF1 gave no end
NEAR = timedelta(minutes=30)
MATCH_WINDOW = timedelta(hours=2)  # OpenF1 start must be this close to ours
FLUSH_DELAY = timedelta(minutes=45)  # free OpenF1 data is available 30 min after the end

# Our session type -> OpenF1 session_name(s)
OPENF1_NAMES: dict[str, tuple[str, ...]] = {
    "FP1": ("Practice 1",),
    "FP2": ("Practice 2",),
    "FP3": ("Practice 3",),
    "SQ": ("Sprint Qualifying", "Sprint Shootout"),
    "SPRINT": ("Sprint",),
    "Q": ("Qualifying",),
    "R": ("Race",),
}

log = structlog.get_logger()


class SessionDirectory(Protocol):
    async def sessions(self, year: int) -> list[dict[str, Any]]: ...


def session_status(now: datetime, s: RaceSession) -> str:
    """Pure transition. Cancelled and finished sessions never change."""
    if s.status in ("cancelled", "finished"):
        return s.status
    end = s.ends_at or s.starts_at + MAX_DURATION
    if now >= end:
        return "finished"
    if now >= s.starts_at - LIVE_LEAD:
        return "live"
    return s.status


def decide_poll_interval(now: datetime, sessions: Sequence[RaceSession]) -> int:
    """Seconds until OpenF1 is worth asking again: 2 while live, 60 within 30 min of a start,
    otherwise 1800."""
    if any(s.status == "live" for s in sessions):
        return 2
    for s in sessions:
        if (
            s.status == "scheduled"
            and s.starts_at - now <= NEAR
            and session_status(now, s) != "finished"
        ):
            return 60
    return 1800


def _ts(raw: Any) -> datetime | None:
    if not raw:
        return None
    return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(UTC)


def match_session_key(
    s: RaceSession, rows: Sequence[dict[str, Any]]
) -> tuple[int, datetime | None] | None:
    """OpenF1 session with a matching name whose start is closest to ours (within 2 h).
    Matching by date, not country: Jolpica and OpenF1 spell countries differently."""
    names = OPENF1_NAMES.get(s.type, ())
    best: tuple[timedelta, int, datetime | None] | None = None
    for r in rows:
        start = _ts(r.get("date_start"))
        if r.get("session_name") not in names or start is None:
            continue
        diff = abs(start - s.starts_at)
        if diff <= MATCH_WINDOW and (best is None or diff < best[0]):
            best = (diff, int(r["session_key"]), _ts(r.get("date_end")))
    return None if best is None else (best[1], best[2])


async def tick_sessions(ctx: dict[str, Any], now: datetime | None = None) -> int:
    """Every minute: advance statuses, resolve OpenF1 keys near a start, enqueue polls and
    post-session flushes. Returns the number of sessions whose status changed."""
    now = now or datetime.now(UTC)
    session_factory = ctx["session_factory"]
    finished: list[uuid.UUID] = []
    live_keys: list[int] = []
    changed = 0
    async with session_factory() as s:
        rows = (
            await s.execute(
                select(RaceSession, Season.year)
                .join(Race, Race.id == RaceSession.race_id)
                .join(Season, Season.id == Race.season_id)
                .where(
                    RaceSession.status.in_(("scheduled", "live")),
                    RaceSession.starts_at.between(now - timedelta(days=1), now + timedelta(days=1)),
                )
            )
        ).all()
        sessions = [rs for rs, _ in rows]
        if decide_poll_interval(now, sessions) <= 60:
            directory: dict[int, list[dict[str, Any]]] = {}
            for rs, year in rows:
                if rs.openf1_session_key is not None or rs.starts_at - now > NEAR:
                    continue
                if year not in directory:
                    try:
                        directory[year] = await ctx["openf1"].sessions(year)
                    except Exception as exc:  # resolve again next tick
                        log.warning("openf1_sessions_failed", year=year, error=str(exc))
                        directory[year] = []
                match = match_session_key(rs, directory[year])
                if match:
                    rs.openf1_session_key, ends_at = match
                    rs.ends_at = ends_at or rs.ends_at
        for rs in sessions:
            new = session_status(now, rs)
            if new != rs.status:
                rs.status = new
                changed += 1
                if new == "finished":
                    finished.append(rs.id)
            if rs.status == "live" and rs.openf1_session_key is not None:
                live_keys.append(rs.openf1_session_key)
        await s.commit()
    arq = ctx["redis"]
    for key in live_keys:  # job id keeps one poller per session
        await arq.enqueue_job("poll_live_session", key, _job_id=f"live:{key}")
    for sid in finished:
        await arq.enqueue_job(
            "flush_live_session", sid, _job_id=f"flush:{sid}", _defer_by=FLUSH_DELAY
        )
    return changed


async def rounds_needing_results(
    session_factory: async_sessionmaker[AsyncSession], year: int
) -> list[int]:
    """Rounds whose race has finished but whose race results are missing or fewer than the
    season's fullest result list (grid size varies by season)."""
    counts = (
        select(Race.round, func.count(SessionResult.id).label("n"))
        .join(Season, Season.id == Race.season_id)
        .join(RaceSession, (RaceSession.race_id == Race.id) & (RaceSession.type == "R"))
        .outerjoin(
            SessionResult,
            (SessionResult.race_id == Race.id) & (SessionResult.session_type == "R"),
        )
        .where(Season.year == year, RaceSession.status == "finished")
        .group_by(Race.round)
    )
    async with session_factory() as s:
        rows = (await s.execute(counts)).all()
    expected = max((n for _, n in rows), default=0)
    return sorted(rnd for rnd, n in rows if n == 0 or n < expected)


async def races_needing_weather(
    session_factory: async_sessionmaker[AsyncSession], today: date
) -> list[uuid.UUID]:
    async with session_factory() as s:
        ids = (
            await s.execute(
                select(Race.id).where(Race.race_date.between(today, today + timedelta(days=7)))
            )
        ).scalars()
        return list(ids)
