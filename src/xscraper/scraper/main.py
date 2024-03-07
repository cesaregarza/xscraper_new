import os
import datetime as dt

from splatnet3_scraper.query import QueryHandler
from dotenv import load_dotenv

from xscraper.scraper.scrape import scrape_all_players_in_mode, get_schedule
from xscraper.scraper.utils import pull_previous_schedule, get_current_rotation_start
from xscraper import constants as xc
from xscraper.scraper.types import Player, Schedule

def scrape(scraper: QueryHandler) -> list[Player]:
    players = []

def main() -> None:
    load_dotenv()
    SCRAPER_CONFIG_PATH = os.getenv("SCRAPER_CONFIG_PATH")
    scraper = QueryHandler.from_config_file(SCRAPER_CONFIG_PATH)
