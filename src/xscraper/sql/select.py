SELECT_CURRENT_SCHEDULE_QUERY = (
    "SELECT * FROM xscraper.schedules "
    "WHERE start_time <= NOW() AND end_time > NOW() "
    "ORDER BY end_time DESC "
    "LIMIT 1"
)

SELECT_PREVIOUS_SCHEDULE_QUERY = (
    "SELECT * FROM xscraper.schedules "
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

SELECT_LATEST_PLAYER_QUERY = (
    "WITH MaxTimestamp AS ("
    "SELECT MAX(timestamp) AS max_timestamp "
    "FROM xscraper.players "
    "WHERE mode = %s "
    "), "
    "FilteredByTimestamp AS ("
    "SELECT player_id, x_power, mode "
    "FROM xscraper.players "
    "WHERE timestamp = (SELECT max_timestamp FROM MaxTimestamp) "
    ") "
    "SELECT * "
    "FROM FilteredByTimestamp "
    "WHERE mode = %s; "
)
