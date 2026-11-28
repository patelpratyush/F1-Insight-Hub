from typing import Literal

from pydantic import BaseModel


class SearchHit(BaseModel):
    kind: Literal["driver", "team", "race"]
    id: str
    label: str
    hint: str | None
    href: str
