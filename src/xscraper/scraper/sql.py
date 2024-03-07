INSERT_PLAYER_QUERY = (
    "INSERT INTO players ("
    "id, name, name_id, rank, x_power, weapon_id, nameplate_id, byname, "
    "text_color, badge_left_id, badge_center_id, badge_right_id, timestamp, "
    "mode, region, "
    "rotation_start, season_number"
    ") "
    "VALUES %s "
    "ON CONFLICT (id, timestamp, mode) DO NOTHING"
)
