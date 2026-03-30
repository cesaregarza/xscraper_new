import datetime as dt
import logging
import time
from typing import Callable

import pytz
from splatnet3_scraper.query import QueryHandler, QueryResponse

from xscraper import constants as xc
from xscraper.scraper.parse import (
    parse_players_in_mode,
    parse_schedule,
    parse_time,
)
from xscraper.scraper.utils import calculate_season_number
from xscraper.types import Mode, Player, Region, Schedule

logger = logging.getLogger(__name__)


def utc_now() -> dt.datetime:
    utc_tz = pytz.timezone("UTC")
    return dt.datetime.now(utc_tz)


def get_current_season(scraper: QueryHandler, region: Region) -> str:
    """Retrieves the current season for a given region using the provided
    scraper.

    Args:
        scraper (QueryHandler): The scraper object used to make the query.
        region (Region): The region for which to retrieve the current season.

    Returns:
        str: The current season for the specified region.
    """
    logger.info("Retrieving current season for %s", region)
    response = scraper.query(xc.query, variables={"region": region})
    return response[xc.current_season_path]


def get_x_ranking_overview(
    scraper: QueryHandler, region: Region
) -> QueryResponse:
    """Retrieve the top-level X ranking overview for a region."""
    logger.info("Retrieving X ranking overview for %s", region)
    return scraper.query(xc.query, variables={"region": region})


def season_final_results_published(data: QueryResponse) -> bool:
    """Return whether a season detail response has published all mode results.

    A season is treated as published once every mode leaderboard has at least
    one edge, which mirrors the data xscraper needs before it can scrape the
    final standings.
    """
    x_ranking = data["xRanking"]
    for mode in xc.modes:
        edges = x_ranking[f"xRanking{mode}", "edges"]
        if len(edges) == 0:
            return False
    return True


def find_past_season(
    scraper: QueryHandler, season_id: str, region: Region
) -> QueryResponse | None:
    """Find a season in the first page of past seasons for a region."""
    overview = get_x_ranking_overview(scraper, region)
    for edge in overview["xRanking", "pastSeasons", "edges"]:
        season = edge["node"]
        if season["id"] == season_id:
            return season
    return None


def wait_for_final_season_results(
    scraper: QueryHandler,
    season_id: str,
    region: Region,
    *,
    poll_interval_seconds: float = 60.0,
    max_attempts: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], dt.datetime] = utc_now,
) -> QueryResponse:
    """Poll until a finished season's final X ranking results are published.

    The function checks each scrape snapshot in order: first it waits for the
    target season to stop being current, then it waits for that season to show
    up in ``pastSeasons``, and finally it confirms the season detail query has
    non-empty results for all four X modes.
    """
    attempts = 0
    while max_attempts is None or attempts < max_attempts:
        attempts += 1
        overview = get_x_ranking_overview(scraper, region)
        current_season = overview["xRanking", "currentSeason"]
        if current_season["id"] == season_id:
            season_end = parse_time(current_season["endTime"])
            if now_fn() < season_end:
                logger.info(
                    "Season %s has not ended yet for %s",
                    season_id,
                    region,
                )
                sleep_fn(poll_interval_seconds)
                continue

        past_season = None
        for edge in overview["xRanking", "pastSeasons", "edges"]:
            season = edge["node"]
            if season["id"] == season_id:
                past_season = season
                break

        if past_season is None:
            logger.info(
                "Season %s is not published in pastSeasons for %s yet",
                season_id,
                region,
            )
            sleep_fn(poll_interval_seconds)
            continue

        detail = scraper.query(
            "XRankingDetailQuery",
            variables={"id": season_id, "region": region},
        )
        if season_final_results_published(detail):
            logger.info(
                "Season %s final results are published for %s",
                season_id,
                region,
            )
            return detail

        logger.info(
            "Season %s detail exists but final results are not fully published "
            "for %s yet",
            season_id,
            region,
        )
        sleep_fn(poll_interval_seconds)

    raise TimeoutError(
        "Season "
        + season_id
        + " final results were not published for "
        + region
        + " before polling stopped."
    )


def pull_detailed_data(
    scraper: QueryHandler,
    season_id: str,
    mode: Mode,
    page: int,
    cursor: str,
    weapons: bool = False,
) -> QueryResponse:
    """Pulls detailed data for a specific season, mode, and page.

    Args:
        scraper (QueryHandler): The scraper object used to make the query.
        season_id (str): The season ID for which to pull the data.
        mode (Mode): The mode for which to pull the data.
        page (int): The page number for which to pull the data.
        cursor (str): The cursor for which to pull the data.
        weapons (bool, optional): If True, pull weapon data. Defaults to False.

    Returns:
        QueryResponse: The response data containing the detailed player
            information.
    """
    logger.info(
        "Pulling detailed data for season %s, mode %s, page %d, cursor %s",
        season_id,
        mode,
        page,
        cursor,
    )
    variables = {
        "id": season_id,
        "mode": mode,
        "page": page,
        "cursor": cursor,
    }
    base_query = xc.detailed_weapon_query if weapons else xc.detailed_x_query
    detailed_query = base_query % mode
    return scraper.query(detailed_query, variables=variables)


def scrape_all_players_in_region_and_mode(
    scraper: QueryHandler, season_id: str, mode: str
) -> list[Player]:
    """Scrapes all players in a specific region and mode for a given season.

    Args:
        scraper (QueryHandler): The scraper object used to make the query.
        season_id (str): The season ID for which to pull the data.
        mode (str): The mode for which to pull the data.

    Returns:
        list[Player]: A list of Player objects containing the scraped player
            data.
    """
    logger.info("Scraping all players in region and mode")
    players = []
    for page in range(1, 6):
        has_next_page = True
        cursor = None
        while has_next_page:
            response = pull_detailed_data(
                scraper=scraper,
                season_id=season_id,
                mode=mode,
                page=page,
                cursor=cursor,
            )
            subresponse = response["node", f"xRanking{mode}"]
            players.extend(parse_players_in_mode(subresponse, mode))
            has_next_page = subresponse["pageInfo", "hasNextPage"]
            cursor = subresponse["pageInfo", "endCursor"]
    return players


def scrape_all_players_in_mode(
    scraper: QueryHandler,
    mode: Mode,
    timestamp: dt.datetime | None = None,
) -> list[Player]:
    """Scrapes all players in a given mode.

    Args:
        scraper (QueryHandler): The query handler object used for scraping.
        mode (Mode): The mode for which players need to be scraped.
        timestamp (datetime.datetime | None, optional): The timestamp to be used
            for player records. Defaults to None.

    Returns:
        list[Player]: A list of Player objects scraped from the given mode.
    """
    out = []
    if timestamp:
        timestamp_insert = timestamp
    else:
        utc_tz = pytz.timezone("UTC")
        timestamp_insert = dt.datetime.now(utc_tz)

    season_number = calculate_season_number(timestamp_insert)
    for region in xc.regions:
        logger.info(
            "Scraping all players in mode %s for region %s", mode, region
        )
        season_id = get_current_season(scraper, region)

        players = []
        players.extend(
            scrape_all_players_in_region_and_mode(scraper, season_id, mode)
        )
        logger.info(
            "Appending timestamp, region, mode, and season number to players"
        )
        for player in players:
            player["timestamp"] = timestamp_insert
            player["region"] = xc.region_map_bool[region]
            player["mode"] = xc.mode_map[mode]
            player["season_number"] = season_number

        out.extend(players)

        logger.info(
            "Scraped all players in mode %s for region %s", mode, region
        )

    return out


def get_schedule(scraper: QueryHandler) -> list[Schedule]:
    """Gets the current schedule from the given query handler.

    Args:
        scraper (QueryHandler): The query handler object used for scraping.

    Returns:
        list[Schedule]: A list of Schedule objects containing the current
            schedule.
    """
    logger.info("Getting the current schedule")
    response = scraper.query(xc.schedule_query)
    return parse_schedule(response)
