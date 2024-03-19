import datetime as dt
import logging
import time

from dotenv import load_dotenv
from psycopg2.extensions import connection as Connection
import sentry_sdk
from splatnet3_scraper.query import QueryHandler

import xscraper.variables as xv
from xscraper.job.utils import load_scrapers, setup_logger
from xscraper.scraper.db import (
    ensure_players_table_exists,
    ensure_schedule_table_exists,
    ensure_schema_exists,
    get_db_connection,
)
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
    last_100_failures = [0] * xv.FAILURE_TRACKER_SIZE
    failure_threshold = int(
        xv.FAILURE_TRACKER_SIZE * xv.FAILURE_THRESHOLD_FLOAT
    )
    while True:
        now = dt.datetime.now()
        cadence_condition = now.minute % scrape_cadence == scrape_offset
        if not cadence_condition and failed_count == 0:
            logger.info("Cadence not met, sleeping for 60 seconds")
            time.sleep(60 - now.second)
            continue
        elif not cadence_condition and failed_count < 2:
            logger.info("Previous scrape failed, attempting again")
            sentry_sdk.capture_message(
                "Previous scrape failed, attempting again. ",
                level="warning",
            )
        elif not cadence_condition and failed_count >= 2:
            logger.error(
                "Previous scrape failed too many times, sleeping for 60 seconds"
            )
            failed_count = 0
            sentry_sdk.capture_message(
                "Scrape failed too many times, skipping this scrape cycle. ",
                level="error",
            )
            time.sleep(60)
            continue
        else:
            logger.info("Cadence met, scraping")

        scraper = get_next_scraper(idx)
        idx += 1
        if idx % num_scrapers == 0:
            idx = 0
        try:
            logger.info("Scraping with scraper %s", scraper)
            scrape(scraper, conn)
            failed_count = 0
            last_100_failures.pop(0)
            last_100_failures.append(0)
            logger.info("Scraping successful")
        except Exception as e:
            logger.error("Scraping failed: %s", e)
            failed_count += 1
            last_100_failures.pop(0)
            last_100_failures.append(1)

            if sum(last_100_failures) >= failure_threshold:
                logger.error(
                    "Failure rate too high, killing the job to prevent "
                    "potential issues. Please check the logs for more "
                    "information."
                )
                raise RuntimeError("Failure rate too high")

        # Sleep until the next minute. It's done minute-by-minute to avoid
        # any issues from extremely long delays.
        time.sleep(60 - dt.datetime.now().second)


def job_with_logging(conn: Connection | None = None) -> None:
    """The main job function that runs the scraping job with logging.

    Args:
        conn (Connection | None): The database connection to use. If None, a new
            connection will be created. Defaults to None.
    """
    setup_logger(
        xv.LOG_FILE_PATH,
        max_bytes=xv.LOG_MAX_BYTES,
        backup_count=xv.LOG_BACKUP_COUNT,
    )
    try:
        job(conn)
    except Exception as e:
        logging.getLogger(__name__).exception("Job failed: %s", e)
        sentry_sdk.capture_exception(e)
        raise e
    finally:
        logging.shutdown()


def setup_db(conn: Connection | None = None) -> None:
    """Sets up the database for the scraping job.

    Args:
        conn (Connection | None): The database connection to use. If None, a new
            connection will be created. Defaults to None.
    """
    logger.info("Setting up the database")
    load_dotenv()
    if conn is None:
        logger.debug("No database connection provided, creating a new one")
        conn = get_db_connection()
    ensure_schema_exists(conn)
    ensure_players_table_exists(conn)
    ensure_schedule_table_exists(conn)


if __name__ == "__main__":
    job()
