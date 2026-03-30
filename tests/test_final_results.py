from __future__ import annotations

import datetime as dt

import pytz
from splatnet3_scraper.query import QueryResponse

from xscraper.scraper.scrape import (
    season_final_results_published,
    wait_for_final_season_results,
)


def make_overview(
    *,
    current_season_id: str,
    current_end_time: str,
    past_season_ids: list[str],
) -> QueryResponse:
    return QueryResponse(
        {
            "xRanking": {
                "currentSeason": {
                    "id": current_season_id,
                    "endTime": current_end_time,
                },
                "pastSeasons": {
                    "edges": [
                        {"node": {"id": season_id}}
                        for season_id in past_season_ids
                    ],
                },
            }
        }
    )


def make_detail(*, populated: bool) -> QueryResponse:
    edge = {
        "node": {
            "id": "player-1",
        }
    }
    return QueryResponse(
        {
            "xRanking": {
                "xRankingAr": {"edges": [edge] if populated else []},
                "xRankingCl": {"edges": [edge] if populated else []},
                "xRankingGl": {"edges": [edge] if populated else []},
                "xRankingLf": {"edges": [edge] if populated else []},
            }
        }
    )


class FakeScraper:
    def __init__(
        self,
        overviews: list[QueryResponse],
        details: list[QueryResponse],
    ) -> None:
        self._overviews = overviews
        self._details = details
        self.overview_calls = 0
        self.detail_calls = 0

    def query(self, query: str, variables: dict | None = None) -> QueryResponse:
        del variables
        if query == "XRankingQuery":
            index = min(self.overview_calls, len(self._overviews) - 1)
            self.overview_calls += 1
            return self._overviews[index]
        if query == "XRankingDetailQuery":
            index = min(self.detail_calls, len(self._details) - 1)
            self.detail_calls += 1
            return self._details[index]
        raise AssertionError(f"Unexpected query: {query}")


def test_season_final_results_published() -> None:
    assert season_final_results_published(make_detail(populated=True)) is True
    assert season_final_results_published(make_detail(populated=False)) is False


def test_wait_for_final_season_results_polls_until_published() -> None:
    season_id = "season-123"
    current_end = "2026-06-01T00:00:00Z"
    next_season_id = "season-124"
    overview_before_publication = make_overview(
        current_season_id=next_season_id,
        current_end_time=current_end,
        past_season_ids=[],
    )
    overview_when_listed = make_overview(
        current_season_id=next_season_id,
        current_end_time=current_end,
        past_season_ids=[season_id],
    )
    scraper = FakeScraper(
        [
            overview_before_publication,
            overview_when_listed,
            overview_when_listed,
        ],
        [
            make_detail(populated=False),
            make_detail(populated=True),
        ],
    )
    sleep_calls: list[float] = []

    result = wait_for_final_season_results(
        scraper,
        season_id,
        "PACIFIC",
        poll_interval_seconds=5.0,
        max_attempts=3,
        sleep_fn=sleep_calls.append,
        now_fn=lambda: dt.datetime(
            2026, 6, 1, 0, 5, tzinfo=pytz.UTC
        ),
    )

    assert season_final_results_published(result) is True
    assert sleep_calls == [5.0, 5.0]


def test_wait_for_final_season_results_times_out_before_end() -> None:
    season_id = "season-123"
    scraper = FakeScraper(
        [
            make_overview(
                current_season_id=season_id,
                current_end_time="2026-06-01T00:00:00Z",
                past_season_ids=[],
            )
        ],
        [],
    )
    sleep_calls: list[float] = []

    try:
        wait_for_final_season_results(
            scraper,
            season_id,
            "PACIFIC",
            poll_interval_seconds=10.0,
            max_attempts=1,
            sleep_fn=sleep_calls.append,
            now_fn=lambda: dt.datetime(
                2026, 5, 31, 23, 59, tzinfo=pytz.UTC
            ),
        )
    except TimeoutError:
        pass
    else:
        raise AssertionError("Expected TimeoutError")

    assert sleep_calls == [10.0]
