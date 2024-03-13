from __future__ import annotations

import datetime as dt
import logging
import os
from typing import TYPE_CHECKING

import pytz
from dotenv import load_dotenv
from splatnet3_scraper.query import QueryHandler

from xscraper import constants as xc
from xscraper.scraper.db import (
    get_db_connection,
    insert_players,
    insert_schedule,
    select_schedule,
)
from xscraper.scraper.scrape import get_schedule, scrape_all_players_in_mode
from xscraper.scraper.utils import (
    calculate_season_number,
    get_current_rotation_start,
    pull_previous_schedule,
)
from xscraper.types import Player, Schedule

if TYPE_CHECKING:
    from psycopg2.extensions import connection as Connection

logger = logging.getLogger(__name__)


def calculate_modes_to_update(
    timestamp: dt.datetime, connection: Connection
) -> list[Schedule]:
    """Calculates the modes to update based on the current time and the
    schedules in the database.

    Args:
        timestamp (dt.datetime): The current timestamp.
        connection (Connection): The database connection to use.

    Returns:
        list[Schedule]: The list of schedules to update. Usually just one, but
            could be two if the timestamp is before 15 minutes into a new
            rotation.
    """
    logger.info("Calculating modes to update")
    out = [select_schedule(connection)]
    if pull_previous_schedule(timestamp):
        logger.info("Pulling previous schedule")
        out.append(select_schedule(timestamp, True))
    return out


def scrape_schedule(scraper: QueryHandler, conn: Connection) -> None:
    """Scrape the schedule and insert it into the database.

    Args:
        scraper (QueryHandler): The query handler to use for scraping.
        conn (Connection): The database connection to use.
    """
    logger.info("Scraping the schedule")
    schedules = get_schedule(scraper)
    logger.info("Inserting the schedule into the database")
    insert_schedule(conn, schedules)


def scrape(scraper: QueryHandler, conn: Connection | None = None) -> None:
    """Scrape the players and insert them into the database.

    Args:
        scraper (QueryHandler): The query handler to use for scraping.
        conn (Connection | None): The database connection to use. If None, a new
            connection will be created. Defaults to None.
    """
    logger.info("Scraping the players")
    utc_tz = pytz.timezone("UTC")
    timestamp = utc_tz.localize(dt.datetime.now())
    players: list[Player] = []
    if conn is None:
        logger.debug("No database connection provided, creating a new one")
        conn = get_db_connection()
    modes_to_update = calculate_modes_to_update(timestamp, conn)

    if modes_to_update[0] is None:
        logger.info(
            "No modes found, scraping the schedule, updating all modes, "
            "and recalculating modes to update"
        )
        scrape_schedule(scraper, conn)
        modes_to_update = calculate_modes_to_update(timestamp, conn)

    for schedule in modes_to_update:
        logger.info("Scraping players for mode %s", schedule["mode"])
        mode = xc.mode_reverse_map[schedule["mode"]]
        players_in_mode = scrape_all_players_in_mode(scraper, mode, timestamp)

        logger.info("Appending rotation start and season number to player data")
        for player in players_in_mode:
            player["rotation_start"] = get_current_rotation_start()
            player["season_number"] = calculate_season_number(timestamp)

        players.extend(players_in_mode)

    logger.info("Inserting players into the database")
    insert_players(conn, players)


def main() -> None:
    """The main function for the scraper."""
    load_dotenv()
    SCRAPER_CONFIG_PATH = os.getenv("SCRAPER_CONFIG_PATH")
    scraper = QueryHandler.from_config_file(SCRAPER_CONFIG_PATH)
