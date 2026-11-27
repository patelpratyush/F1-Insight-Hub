from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Kind = Literal["position", "lap", "interval", "stint", "pit", "flag", "weather", "status"]


@dataclass(frozen=True)
class LiveEvent:
    seq: int
    ts: datetime
    kind: Kind
    driver_number: int | None
    data: Mapping[str, object]
