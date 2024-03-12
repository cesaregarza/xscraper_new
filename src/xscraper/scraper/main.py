from __future__ import annotations

import datetime as dt
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
from xscraper.types import Player, Schedule
from xscraper.scraper.utils import (
    calculate_season_number,
    get_current_rotation_start,
    pull_previous_schedule,
)

if TYPE_CHECKING:
    from psycopg2.extensions import connection as Connection


def calculate_modes_to_update(
    timestamp: dt.datetime, connection: Connection
) -> list[Schedule]:
    out = [select_schedule(connection)]
    if pull_previous_schedule(timestamp):
        out.append(select_schedule(timestamp, True))
    return out


def scrape_schedule(scraper: QueryHandler, conn: Connection) -> None:
    schedules = get_schedule(scraper)
    insert_schedule(conn, schedules)


def scrape(
    scraper: QueryHandler, conn: Connection | None = None
) -> list[Player]:
    utc_tz = pytz.timezone("UTC")
    timestamp = utc_tz.localize(dt.datetime.now())
    players: list[Player] = []
    if conn is None:
        conn = get_db_connection()
    modes_to_update = calculate_modes_to_update(timestamp, conn)

    if modes_to_update[0] is None:
        scrape_schedule(scraper, conn)
        modes_to_update = calculate_modes_to_update(timestamp, conn)

    for schedule in modes_to_update:
        mode = xc.mode_reverse_map[schedule["mode"]]
        players_in_mode = scrape_all_players_in_mode(scraper, mode, timestamp)

        for player in players_in_mode:
            player["rotation_start"] = get_current_rotation_start()
            player["season_number"] = calculate_season_number(timestamp)

        players.extend(players_in_mode)

    insert_players(conn, players)


def main() -> None:
    load_dotenv()
    SCRAPER_CONFIG_PATH = os.getenv("SCRAPER_CONFIG_PATH")
    scraper = QueryHandler.from_config_file(SCRAPER_CONFIG_PATH)
