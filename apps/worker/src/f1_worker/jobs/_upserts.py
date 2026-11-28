"""Idempotent upserts for reference rows shared by ingestion jobs."""

import uuid

from f1_core.ids import uuid7
from f1_db.base import utcnow
from f1_db.models import Driver, Season, Team
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

SOURCE = "jolpica"


async def upsert_season(s: AsyncSession, year: int) -> uuid.UUID:
    await s.execute(
        insert(Season).values(id=uuid7(), year=year).on_conflict_do_nothing(index_elements=["year"])
    )
    return (await s.execute(select(Season.id).where(Season.year == year))).scalar_one()


async def upsert_team(s: AsyncSession, ref: str, name: str, nationality: str | None) -> uuid.UUID:
    await s.execute(
        insert(Team)
        .values(
            id=uuid7(),
            ref=ref,
            name=name,
            nationality=nationality,
            source=SOURCE,
            ingested_at=utcnow(),
        )
        .on_conflict_do_update(
            index_elements=["ref"], set_={"name": name, "nationality": nationality}
        )
    )
    return (await s.execute(select(Team.id).where(Team.ref == ref))).scalar_one()


async def upsert_driver(
    s: AsyncSession,
    ref: str,
    code: str | None,
    given_name: str,
    family_name: str,
    number: int | None,
    nationality: str | None,
) -> uuid.UUID:
    await s.execute(
        insert(Driver)
        .values(
            id=uuid7(),
            ref=ref,
            code=code,
            given_name=given_name,
            family_name=family_name,
            number=number,
            nationality=nationality,
            source=SOURCE,
            ingested_at=utcnow(),
        )
        .on_conflict_do_update(
            index_elements=["ref"],
            set_={
                "code": code,
                "number": number,
                "given_name": given_name,
                "family_name": family_name,
            },
        )
    )
    return (await s.execute(select(Driver.id).where(Driver.ref == ref))).scalar_one()
