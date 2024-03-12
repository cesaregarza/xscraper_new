INSERT_PLAYER_QUERY = (
    "INSERT INTO xscraper.players ("
    "player_id, name, name_id, rank, x_power, weapon_id, nameplate_id, byname, "
    "text_color, badge_left_id, badge_center_id, badge_right_id, timestamp, "
    "mode, region, "
    "rotation_start, season_number"
    ") "
    "VALUES %s "
    "ON CONFLICT (player_id, timestamp, mode) DO NOTHING"
)

INSERT_SCHEDULE_QUERY = (
    "INSERT INTO xscraper.schedules ("
    "start_time, end_time, splatfest, mode, stage_1_id, stage_1_name, "
    "stage_2_id, stage_2_name"
    ") "
    "VALUES %s "
    "ON CONFLICT (start_time, end_time) DO NOTHING"
)
