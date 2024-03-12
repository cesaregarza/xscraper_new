ENSURE_SCHEMA_QUERY = "CREATE SCHEMA IF NOT EXISTS xscraper"

ENSURE_TRGM_EXTENSION_QUERY = "CREATE EXTENSION IF NOT EXISTS pg_trgm"

ENSURE_PLAYER_TABLE_QUERY = (
    "CREATE TABLE IF NOT EXISTS xscraper.players ("
    "player_id TEXT PRIMARY KEY, "
    "name TEXT NOT NULL, "
    "name_id TEXT NOT NULL, "
    "splashtag TEXT UNIQUE NOT NULL, "
    "rank INTEGER NOT NULL, "
    "x_power FLOAT NOT NULL, "
    "weapon_id INTEGER NOT NULL, "
    "nameplate_id INTEGER, "
    "byname TEXT, "
    "text_color TEXT, "
    "badge_left_id INTEGER, "
    "badge_center_id INTEGER, "
    "badge_right_id INTEGER, "
    "timestamp TIMESTAMP WITH TIME ZONE NOT NULL, "
    "mode xscraper.mode_name, "
    "region BOOLEAN NOT NULL, "
    "rotation_start TIMESTAMP WITH TIME ZONE, "
    "season_number INTEGER, "
    "CONSTRAINT pk_player_timestamp UNIQUE (player_id, timestamp, mode)"
    ")"
)

CREATE_MODE_ENUM_QUERY = (
    "DO $$ BEGIN "
    "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mode_name') THEN "
    "CREATE TYPE xscraper.mode_name AS ENUM ("
    "'Splat Zones',"
    "'Clam Blitz',"
    "'Rainmaker',"
    "'Tower Control'"
    "); "
    "END IF; "
    "END $$"
)

ENSURE_PLAYER_INDEX_SPLASHTAG_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_splashtag_gin "
    "ON xscraper.players USING GIN (splashtag gin_trgm_ops)"
)

ENSURE_PLAYER_INDEX_TIMESTAMP_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_timestamp "
    "ON xscraper.players (timestamp)"
)

ENSURE_PLAYER_INDEX_MODE_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_mode " "ON xscraper.players (mode)"
)

ENSURE_PLAYER_INDEX_REGION_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_region "
    "ON xscraper.players (region)"
)

ENSURE_PLAYER_INDEX_ROTATION_START_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_rotation_start "
    "ON xscraper.players (rotation_start)"
)

ENSURE_PLAYER_INDEX_SEASON_NUMBER_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_season_number "
    "ON xscraper.players (season_number)"
)

ENSURE_PLAYER_INDEX_MODE_TIMESTAMP_SEASON_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_players_mode_timestamp_season_number "
    "ON xscraper.players (mode, timestamp, season_number)"
)

ENSURE_PLAYER_INDEX_QUERIES = [
    ENSURE_PLAYER_INDEX_SPLASHTAG_QUERY,
    ENSURE_PLAYER_INDEX_TIMESTAMP_QUERY,
    ENSURE_PLAYER_INDEX_MODE_QUERY,
    ENSURE_PLAYER_INDEX_REGION_QUERY,
    ENSURE_PLAYER_INDEX_ROTATION_START_QUERY,
    ENSURE_PLAYER_INDEX_SEASON_NUMBER_QUERY,
    ENSURE_PLAYER_INDEX_MODE_TIMESTAMP_SEASON_QUERY,
]

ENSURE_SCHEDULE_TABLE_QUERY = (
    "CREATE TABLE IF NOT EXISTS xscraper.schedules ("
    "start_time TIMESTAMP WITH TIME ZONE NOT NULL PRIMARY KEY, "
    "end_time TIMESTAMP WITH TIME ZONE NOT NULL, "
    "splatfest BOOLEAN, "
    "mode xscraper.mode_name, "
    "stage_1_id INTEGER, "
    "stage_1_name TEXT, "
    "stage_2_id INTEGER, "
    "stage_2_name TEXT, "
    "CONSTRAINT sc_start_time_end_time UNIQUE (start_time, end_time)"
    ")"
)

ENSURE_SCHEDULE_INDEX_START_TIME_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_schedules_start_time "
    "ON xscraper.schedules (start_time)"
)

ENSURE_SCHEDULE_INDEX_END_TIME_QUERY = (
    "CREATE INDEX IF NOT EXISTS idx_schedules_end_time "
    "ON xscraper.schedules (end_time)"
)

ENSURE_SCHEDULE_INDEX_QUERIES = [
    ENSURE_SCHEDULE_INDEX_START_TIME_QUERY,
    ENSURE_SCHEDULE_INDEX_END_TIME_QUERY,
]
