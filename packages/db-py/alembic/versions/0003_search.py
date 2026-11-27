"""search

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-27 17:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = [
    ("ix_drivers_family_name_trgm", "drivers", "family_name"),
    ("ix_drivers_given_name_trgm", "drivers", "given_name"),
    ("ix_teams_name_trgm", "teams", "name"),
    ("ix_races_name_trgm", "races", "name"),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for name, table, column in INDEXES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {name} ON {table} USING gin ({column} gin_trgm_ops)"
        )


def downgrade() -> None:
    for name, _, _ in INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
    # Extensions are left installed; other objects may depend on them.
