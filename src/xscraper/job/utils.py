import logging
import os
import pathlib
from logging.handlers import RotatingFileHandler

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
    for i in range(10):
        logger.debug("Loading scraper %d", i)
        path = f"SCRAPER_{i}.ini"
        if os.path.exists(path):
            scrapers.append(QueryHandler.from_config_file(path))
        else:
            logger.warning("Path %s does not exist. Stopping", path)
            break

    return scrapers


def setup_logger(
    log_file_path: str,
    max_bytes: int = 1024 * 1024,
    backup_count: int = 5,
    level: int = logging.INFO,
) -> None:
    """Sets up a logger that dumps to a new file every time the log file reaches
    a certain size.

    Args:
        log_file_path (str): The path to the log file.
        max_bytes (int, optional): The maximum size in bytes before the log file
            is rotated. Defaults to 1MB (1024 * 1024).
        backup_count (int, optional): The number of backup files to keep.
            Defaults to 5.
        level (int, optional): The logging level. Defaults to logging.INFO.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Make sure the directory exists
    pathlib.Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Create a RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(level)

    # Create a StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add the handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
