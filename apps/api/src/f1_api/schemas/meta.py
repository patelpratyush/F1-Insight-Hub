from datetime import datetime

from pydantic import BaseModel


class FreshnessOut(BaseModel):
    job: str
    last_success_at: datetime | None
    last_status: str
