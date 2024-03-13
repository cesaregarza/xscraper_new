import logging
import os

from splatnet3_scraper.query import QueryHandler

logger = logging.getLogger(__name__)


def load_scrapers() -> list[QueryHandler]:
    """Loads the scrapers from the environment variables.

    This function loads the scrapers by retrieving the number of scrapers from
    the environment variable 'NUM_SCRAPERS'. It then iterates over the range of
    the number of scrapers and checks if the corresponding environment variable
    'SCRAPER_{i}_PATH' is set. If the environment variable is set, it creates a
    QueryHandler object using the path specified in the environment variable and
    appends it to the 'scrapers' list. If the environment variable is not set
    and the index is 0, it raises a ValueError indicating that at least one
    scraper should be set.

    Returns:
        list[QueryHandler]: A list of QueryHandler objects representing the
            loaded scrapers.
    """
    scrapers = []
    num_scrapers = int(os.getenv("NUM_SCRAPERS", 1))
    logger.info("Loading %d scrapers", num_scrapers)
    for i in range(num_scrapers):
        logger.debug("Loading scraper %d", i)
        env_path = f"SCRAPER_{i}_PATH"
        if (path := os.getenv(env_path)) is not None:
            scrapers.append(QueryHandler.from_config_file(path))
        elif i == 0:
            logger.error("No scrapers found. Please set at least one scraper.")
            raise ValueError(
                "No scrapers found. Please set at least one scraper."
            )
    return scrapers
