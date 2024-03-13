import datetime as dt
import time

from dotenv import load_dotenv
from psycopg2.extensions import connection as Connection
from splatnet3_scraper.query import QueryHandler

import xscraper.variables as xv
from xscraper.job.utils import load_scrapers
from xscraper.scraper.main import scrape


def job(conn: Connection | None = None) -> None:
    """The main job function that runs the scraping job.

    Args:
        conn (Connection | None): The database connection to use. If None, a new
            connection will be created. Defaults to None.
    """
    load_dotenv()
    scrapers = load_scrapers()
    num_scrapers = len(scrapers)

    def get_next_scraper(idx: int) -> QueryHandler:
        return scrapers[idx % num_scrapers]

    scrape_cadence = xv.SCRAPE_CADENCE.total_seconds() / 60
    scrape_offset = xv.SCRAPE_OFFSET_MINUTES.total_seconds() / 60
    idx = 0
    while True:
        scraper = get_next_scraper(idx)
        idx += 1
        if idx % num_scrapers == 0:
            idx = 0
        now = dt.datetime.now()
        if now.minute % scrape_cadence == scrape_offset:
            scrape(scraper, conn)
        time.sleep(60 - dt.datetime.now().second)


if __name__ == "__main__":
    job()
