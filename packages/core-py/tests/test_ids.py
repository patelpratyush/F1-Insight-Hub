import time
import uuid

from f1_core.ids import uuid7


def test_uuid7_has_version_7_and_rfc_variant() -> None:
    value = uuid7()
    assert isinstance(value, uuid.UUID)
    assert value.version == 7
    assert value.variant == uuid.RFC_4122


def test_uuid7_is_time_ordered() -> None:
    first = uuid7()
    time.sleep(0.005)
    second = uuid7()
    assert first.int < second.int


def test_uuid7_is_unique_across_many_calls() -> None:
    assert len({uuid7() for _ in range(10_000)}) == 10_000
