import datetime as dt
import os

from dotenv import load_dotenv
from splatnet3_scraper.query import QueryHandler

from xscraper import constants as xc
from xscraper.scraper.scrape import get_schedule, scrape_all_players_in_mode
from xscraper.scraper.types import Player, Schedule
from xscraper.scraper.utils import (
    get_current_rotation_start,
    pull_previous_schedule,
)


def scrape(scraper: QueryHandler) -> list[Player]:
    players = []


def main() -> None:
    load_dotenv()
    SCRAPER_CONFIG_PATH = os.getenv("SCRAPER_CONFIG_PATH")
    scraper = QueryHandler.from_config_file(SCRAPER_CONFIG_PATH)
