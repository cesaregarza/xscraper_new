SELECT_CURRENT_SCHEDULE_QUERY = (
    "SELECT * FROM xscraper.schedule "
    "WHERE start_time <= NOW() AND end_time > NOW() "
    "ORDER BY end_time DESC "
    "LIMIT 1"
)

SELECT_PREVIOUS_SCHEDULE_QUERY = (
    "SELECT * FROM xscraper.schedule "
    "WHERE end_time < NOW() "
    "ORDER BY end_time DESC "
    "LIMIT 1"
)

SELECT_MAX_TIMESTAMP_AND_MODE_QUERY = (
    "SELECT timestamp, mode "
    "FROM xscraper.players "
    "ORDER BY timestamp DESC "
    "LIMIT 1"
)
