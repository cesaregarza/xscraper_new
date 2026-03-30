from __future__ import annotations

from xscraper.scraper.db import ensure_schedule_table_exists
from xscraper.sql.ensure import (
    ENSURE_SCHEDULE_INDEX_QUERIES,
    ENSURE_SCHEDULE_TABLE_QUERY,
)


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, query: str) -> None:
        self.executed.append(query)

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.commit_count = 0

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def test_ensure_schedule_table_uses_schedule_indexes() -> None:
    connection = FakeConnection()

    ensure_schedule_table_exists(connection)

    assert connection.cursor_instance.executed[0] == ENSURE_SCHEDULE_TABLE_QUERY
    assert (
        connection.cursor_instance.executed[1:]
        == ENSURE_SCHEDULE_INDEX_QUERIES
    )
    assert connection.commit_count == 1
