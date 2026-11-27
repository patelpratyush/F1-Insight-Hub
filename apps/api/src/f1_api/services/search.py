from typing import Any

from f1_db.models import Driver, Race, Season, Team
from sqlalchemy import case, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from f1_api.schemas.search import SearchHit

LIMIT = 20


def _escape(q: str) -> str:
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SearchService:
    """Accent- and case-insensitive ILIKE search. Rank 0 = prefix match, 1 = substring.

    shortcut: the pg_trgm indexes cover the raw columns, not unaccent(column), so they are
    not used by these queries; add immutable unaccent expression indexes if search gets slow.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(self, q: str) -> list[SearchHit]:
        esc = _escape(q)
        prefix = func.unaccent(literal(esc + "%"))
        contains = func.unaccent(literal("%" + esc + "%"))

        def match(*cols: Any) -> tuple[Any, Any]:
            un = [func.unaccent(c) for c in cols]
            hit = or_(*(u.ilike(contains, escape="\\") for u in un))
            rank = case((or_(*(u.ilike(prefix, escape="\\") for u in un)), 0), else_=1)
            return hit, rank

        full_name = Driver.given_name + " " + Driver.family_name
        d_hit, d_rank = match(Driver.family_name, Driver.given_name, full_name)
        t_hit, t_rank = match(Team.name)
        r_hit, r_rank = match(Race.name)

        hits: list[tuple[int, SearchHit]] = []
        for d, rank in (await self.session.execute(select(Driver, d_rank).where(d_hit))).all():
            hits.append(
                (
                    rank,
                    SearchHit(
                        kind="driver",
                        id=str(d.id),
                        label=f"{d.given_name} {d.family_name}",
                        hint=d.code,
                        href=f"/drivers/{d.ref}",
                    ),
                )
            )
        for t, rank in (await self.session.execute(select(Team, t_rank).where(t_hit))).all():
            hits.append(
                (
                    rank,
                    SearchHit(
                        kind="team",
                        id=str(t.id),
                        label=t.name,
                        hint=t.nationality,
                        href=f"/teams/{t.ref}",
                    ),
                )
            )
        races = await self.session.execute(
            select(Race, Season.year, r_rank)
            .join(Season, Season.id == Race.season_id)
            .where(r_hit)
            .order_by(Season.year.desc())
        )
        for r, year, rank in races.all():
            hits.append(
                (
                    rank,
                    SearchHit(
                        kind="race",
                        id=str(r.id),
                        label=r.name,
                        hint=str(year),
                        href=f"/races/{year}/{r.round}",
                    ),
                )
            )
        # Stable sort keeps newer seasons first among same-named races.
        hits.sort(key=lambda h: (h[0], h[1].label))
        return [h for _, h in hits[:LIMIT]]
