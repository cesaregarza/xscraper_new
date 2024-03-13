import datetime as dt
import logging

import pytz
from splatnet3_scraper.query import QueryHandler, QueryResponse

from xscraper import constants as xc
from xscraper.scraper.parse import parse_players_in_mode, parse_schedule
from xscraper.scraper.utils import calculate_season_number
from xscraper.types import Mode, Player, Region, Schedule

logger = logging.getLogger(__name__)


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
