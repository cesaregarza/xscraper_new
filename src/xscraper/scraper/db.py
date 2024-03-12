from __future__ import annotations

import os
from typing import TYPE_CHECKING

import psycopg2
from psycopg2.extras import execute_values

from xscraper.scraper.types import Player, Schedule
from xscraper.sql.ensure import (
    CREATE_MODE_ENUM_QUERY,
    ENSURE_PLAYER_INDEX_QUERIES,
    ENSURE_PLAYER_TABLE_QUERY,
    ENSURE_SCHEDULE_TABLE_QUERY,
    ENSURE_SCHEMA_QUERY,
    ENSURE_TRGM_EXTENSION_QUERY,
)
from xscraper.sql.functions import FUNCTION_SPLASHTAG_QUERY
from xscraper.sql.insert import INSERT_PLAYER_QUERY, INSERT_SCHEDULE_QUERY
from xscraper.sql.select import (
    SELECT_CURRENT_SCHEDULE_QUERY,
    SELECT_MAX_TIMESTAMP_AND_MODE_QUERY,
    SELECT_PREVIOUS_SCHEDULE_QUERY,
)
from xscraper.sql.triggers import TRIGGER_SPLASHTAG_QUERY

if TYPE_CHECKING:
    from psycopg2.extensions import connection as Connection


def get_db_credentials() -> dict[str, str]:
    return {
        "dbname": os.getenv("POSTGRES_NAME"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
    }


def get_db_connection(**kwargs) -> Connection:
    return psycopg2.connect(**get_db_credentials(), **kwargs)


def insert_players(conn: Connection, players: list[Player]) -> None:
    with conn.cursor() as cursor:
        values = [
            (
                player["id"],
                player["name"],
                player["name_id"],
                player["rank"],
                player["x_power"],
                player["weapon_id"],
                player["nameplate_id"],
                player["byname"],
                player["text_color"],
                player.get("badge_left_id"),
                player.get("badge_center_id"),
                player.get("badge_right_id"),
                player["timestamp"],
                player["mode"],
                player["region"],
                player["rotation_start"],
                player["season_number"],
            )
            for player in players
        ]
        execute_values(cursor, INSERT_PLAYER_QUERY, values)
        conn.commit()


def insert_schedule(conn: Connection, schedules: list[Schedule]) -> None:
    with conn.cursor() as cursor:
        values = [
            (
                schedule["start_time"],
                schedule["end_time"],
                schedule["splatfest"],
                schedule.get("mode"),
                schedule.get("stage_1_id"),
                schedule.get("stage_1_name"),
                schedule.get("stage_2_id"),
                schedule.get("stage_2_name"),
            )
            for schedule in schedules
        ]
        execute_values(cursor, INSERT_SCHEDULE_QUERY, values)
        conn.commit()


def select_schedule(conn: Connection, previous: bool = False) -> Schedule:
    query = (
        SELECT_PREVIOUS_SCHEDULE_QUERY
        if previous
        else SELECT_CURRENT_SCHEDULE_QUERY
    )
    with conn.cursor() as cursor:
        cursor.execute(query)
        value = cursor.fetchone()
        if value is None or len(value) == 0:
            return None
        return Schedule(
            start_time=value[0],
            end_time=value[1],
            splatfest=value[2],
            mode=value[3],
            stage_1_id=value[4],
            stage_1_name=value[5],
            stage_2_id=value[6],
            stage_2_name=value[7],
        )


def select_latest_timestamp(conn: Connection) -> str:
    with conn.cursor() as cursor:
        cursor.execute(SELECT_MAX_TIMESTAMP_AND_MODE_QUERY)
        return cursor.fetchone()


def ensure_schema_exists(conn: Connection) -> None:
    with conn.cursor() as cursor:
        cursor.execute(ENSURE_SCHEMA_QUERY)
        cursor.execute(CREATE_MODE_ENUM_QUERY)
        cursor.execute(ENSURE_TRGM_EXTENSION_QUERY)
        conn.commit()


def ensure_players_table_exists(conn: Connection) -> None:
    with conn.cursor() as cursor:
        cursor.execute(ENSURE_PLAYER_TABLE_QUERY)
        cursor.execute(FUNCTION_SPLASHTAG_QUERY)
        conn.commit()
        try:
            cursor.execute(TRIGGER_SPLASHTAG_QUERY)
        except psycopg2.errors.DuplicateObject:
            conn.rollback()
        for query in ENSURE_PLAYER_INDEX_QUERIES:
            cursor.execute(query)
        conn.commit()


def ensure_schedule_table_exists(conn: Connection) -> None:
    with conn.cursor() as cursor:
        cursor.execute(ENSURE_SCHEDULE_TABLE_QUERY)
        for query in ENSURE_PLAYER_INDEX_QUERIES:
            cursor.execute(query)
        conn.commit()
