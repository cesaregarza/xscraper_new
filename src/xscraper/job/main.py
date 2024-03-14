import datetime as dt
import logging
import time

from dotenv import load_dotenv
from psycopg2.extensions import connection as Connection
from splatnet3_scraper.query import QueryHandler

import xscraper.variables as xv
from xscraper.job.utils import load_scrapers
from xscraper.scraper.main import scrape

logger = logging.getLogger(__name__)


def job(conn: Connection | None = None) -> None:
    """The main job function that runs the scraping job.

    Args:
        conn (Connection | None): The database connection to use. If None, a new
            connection will be created. Defaults to None.
    """
    logger.info("Starting the scraping job")
    load_dotenv()
    logger.info("Loading the scrapers")
    scrapers = load_scrapers()
    num_scrapers = len(scrapers)
    logger.info("Loaded %d scrapers", num_scrapers)

    def get_next_scraper(idx: int) -> QueryHandler:
        logger.info("Loading scraper %d", idx % num_scrapers)
        return scrapers[idx % num_scrapers]

    scrape_cadence = xv.SCRAPE_CADENCE.total_seconds() / 60
    scrape_offset = xv.SCRAPE_OFFSET_MINUTES.total_seconds() / 60
    idx = 0
    failed_count = 0
    while True:
        now = dt.datetime.now()
        cadence_condition = now.minute % scrape_cadence == scrape_offset
        if not cadence_condition and failed_count == 0:
            logger.info("Cadence not met, sleeping for 60 seconds")
            time.sleep(60)
            continue
        elif not cadence_condition and failed_count < 2:
            logger.info("Previous scrape failed, attempting again")
        elif not cadence_condition and failed_count >= 2:
            logger.error(
                "Previous scrape failed too many times, sleeping for 60 seconds"
            )
            failed_count = 0
            time.sleep(60)
            continue
        else:
            logger.info("Cadence met, scraping")

        scraper = get_next_scraper(idx)
        idx += 1
        if idx % num_scrapers == 0:
            idx = 0
        try:
            scrape(scraper, conn)
            failed_count = 0
        except Exception as e:
            logger.error("Scraping failed: %s", e)
            failed_count += 1

        # Sleep until the next minute. It's done minute-by-minute to avoid
        # any issues from extremely long delays.
        time.sleep(60 - dt.datetime.now().second)


def job_with_logging(conn: Connection | None = None) -> None:
    """The main job function that runs the scraping job with logging.

    Args:
        conn (Connection | None): The database connection to use. If None, a new
            connection will be created. Defaults to None.
    """
    logging.basicConfig(level=logging.INFO)
    job(conn)


if __name__ == "__main__":
    job()
