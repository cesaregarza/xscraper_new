from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING

import pytz
from dotenv import load_dotenv
from splatnet3_scraper.query import QueryHandler

from xscraper import constants as xc
from xscraper.scraper.db import get_db_connection, get_schedule
from xscraper.scraper.scrape import get_schedule, scrape_all_players_in_mode
from xscraper.scraper.types import Player, Schedule
from xscraper.scraper.utils import (
    get_current_rotation_start,
    pull_previous_schedule,
)

if TYPE_CHECKING:
    from psycopg2.extensions import connection as Connection


def calculate_modes_to_update(
    timestamp: dt.datetime, connection: Connection
) -> list[Schedule]:
    out = [get_schedule(connection)]
    if pull_previous_schedule(timestamp):
        out.append(pull_previous_schedule(timestamp))
    return out


def scrape(scraper: QueryHandler) -> list[Player]:
    utc_tz = pytz.timezone("UTC")
    timestamp = utc_tz.localize(dt.datetime.now())
    players: list[Player] = []
    conn = get_db_connection()


def main() -> None:
    load_dotenv()
    SCRAPER_CONFIG_PATH = os.getenv("SCRAPER_CONFIG_PATH")
    scraper = QueryHandler.from_config_file(SCRAPER_CONFIG_PATH)
