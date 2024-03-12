import os

from splatnet3_scraper.query import QueryHandler


def load_scrapers() -> list[QueryHandler]:
    scrapers = []
    num_scrapers = int(os.getenv("NUM_SCRAPERS", 1))
    for i in range(num_scrapers):
        env_path = f"SCRAPER_{i}_PATH"
        if (path := os.getenv(env_path)) is not None:
            scrapers.append(QueryHandler.from_config_file(path))
        elif i == 0:
            raise ValueError(
                "No scrapers found. Please set at least one scraper."
            )
    return scrapers
