INSERT_PLAYER_QUERY = (
    "INSERT INTO xscraper.players ("
    "id, name, name_id, rank, x_power, weapon_id, nameplate_id, byname, "
    "text_color, badge_left_id, badge_center_id, badge_right_id, timestamp, "
    "mode, region, "
    "rotation_start, season_number"
    ") "
    "VALUES %s "
    "ON CONFLICT (id, timestamp, mode) DO NOTHING"
)

INSERT_SCHEDULE_QUERY = (
    "INSERT INTO xscraper.schedule ("
    "start_time, end_time, splatfest, mode, stage_1_id, stage_1_name, "
    "stage_2_id, stage_2_name"
    ") "
    "VALUES %s "
    "ON CONFLICT (start_time, end_time) DO NOTHING"
)

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
