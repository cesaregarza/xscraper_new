import datetime as dt

# Defineable constants
SCRAPE_CADENCE = dt.timedelta(minutes=10)
SCRAPE_OFFSET_MINUTES = dt.timedelta(minutes=4)
LOG_FILE_PATH = "logs/scraping.log"
LOG_MAX_BYTES = 1024 * 1024  # 1MB
LOG_BACKUP_COUNT = 5
FAILURE_TRACKER_SIZE = 30
FAILURE_THRESHOLD_FLOAT = 0.5
