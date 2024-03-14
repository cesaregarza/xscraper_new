from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import psycopg2
from psycopg2.extras import execute_values

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
    SELECT_LATEST_PLAYER_QUERY,
    SELECT_MAX_TIMESTAMP_AND_MODE_QUERY,
    SELECT_PREVIOUS_SCHEDULE_QUERY,
)
from xscraper.sql.triggers import TRIGGER_SPLASHTAG_QUERY
from xscraper.types import Player, Schedule

if TYPE_CHECKING:
    from psycopg2.extensions import connection as Connection

logger = logging.getLogger(__name__)


def get_db_credentials() -> dict[str, str]:
    """Get the database credentials from the environment variables.

    Environment Variables:
        - POSTGRES_NAME: The name of the PostgreSQL db.
        - POSTGRES_USER: The username for connecting to the PostgreSQL db.
        - POSTGRES_PASSWORD: The password for connecting to the PostgreSQL db.
        - POSTGRES_HOST: The host address of the PostgreSQL db.
        - POSTGRES_PORT: The port number for connecting to the PostgreSQL db.

    Returns:
        dict[str, str]: The database credentials.
    """
    logger.debug("Getting database credentials from environment variables")
    return {
        "dbname": os.getenv("POSTGRES_NAME"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
    }


def get_db_connection(**kwargs) -> Connection:
    """Get a connection to the PostgreSQL database.

    Args:
        **kwargs: Additional keyword arguments to pass to the psycopg2.connect
            function.

    Returns:
        Connection: The connection to the PostgreSQL database.
    """
    logger.debug("Getting a connection to the PostgreSQL database")
    return psycopg2.connect(**get_db_credentials(), **kwargs)


def insert_players(conn: Connection, players: list[Player]) -> None:
    """Insert the given players into the database.

    Args:
        conn (Connection): The database connection to use.
        players (list[Player]): The list of players to insert into the database.
    """
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
                player["updated"],
            )
            for player in players
        ]
        logger.info("Inserting %d players into the database", len(values))
        execute_values(cursor, INSERT_PLAYER_QUERY, values)
        logger.info("Committing the transaction to the database")
        conn.commit()


def insert_schedule(conn: Connection, schedules: list[Schedule]) -> None:
    """Insert the given schedules into the database.

    Args:
        conn (Connection): The database connection to use.
        schedules (list[Schedule]): The list of schedules to insert into the
            database.
    """
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
        logger.info("Inserting %d schedules into the database", len(values))
        execute_values(cursor, INSERT_SCHEDULE_QUERY, values)
        logger.info("Committing the transaction to the database")
        conn.commit()


def select_schedule(conn: Connection, previous: bool = False) -> Schedule:
    """Select the current or previous schedule from the database.

    Args:
        conn (Connection): The database connection to use.
        previous (bool): Whether to select the previous schedule instead of the
            current schedule.

    Returns:
        Schedule: The current or previous schedule from the database.
    """
    query = (
        SELECT_PREVIOUS_SCHEDULE_QUERY
        if previous
        else SELECT_CURRENT_SCHEDULE_QUERY
    )
    logger.debug(
        "Selecting the %s schedule from the database",
        "previous" if previous else "current",
    )
    with conn.cursor() as cursor:
        logger.debug("Pulling the schedule from the database")
        cursor.execute(query)
        value = cursor.fetchone()
        if value is None or len(value) == 0:
            logger.warning("No schedule found in the database")
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
    """Select the latest timestamp from the database.

    Args:
        conn (Connection): The database connection to use.

    Returns:
        str: The latest timestamp.
    """
    logger.debug("Selecting the latest timestamp from the database")
    with conn.cursor() as cursor:
        cursor.execute(SELECT_MAX_TIMESTAMP_AND_MODE_QUERY)
        return cursor.fetchone()


def select_latest_players(conn: Connection, mode: str) -> list[Player]:
    """Select the latest players from the database.

    Args:
        conn (Connection): The database connection to use.
        mode (str): The mode to select the latest players for.

    Returns:
        list[Player]: The latest players from the database.
    """
    logger.debug("Selecting the latest players from the database")
    with conn.cursor() as cursor:
        cursor.execute(SELECT_LATEST_PLAYER_QUERY, (mode, mode))
        return cursor.fetchall()


def ensure_schema_exists(conn: Connection) -> None:
    """Ensure that the database schema exists.

    Args:
        conn (Connection): The database connection to use.
    """
    logger.debug("Ensuring that the database schema exists")
    with conn.cursor() as cursor:
        cursor.execute(ENSURE_SCHEMA_QUERY)
        cursor.execute(CREATE_MODE_ENUM_QUERY)
        cursor.execute(ENSURE_TRGM_EXTENSION_QUERY)
        conn.commit()


def ensure_players_table_exists(conn: Connection) -> None:
    """Ensure that the players table exists in the database.

    Args:
        conn (Connection): The database connection to use.
    """
    logger.debug("Ensuring that the players table exists in the database")
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
    """Ensure that the schedule table exists in the database.

    Args:
        conn (Connection): The database connection to use.
    """
    logger.debug("Ensuring that the schedule table exists in the database")
    with conn.cursor() as cursor:
        cursor.execute(ENSURE_SCHEDULE_TABLE_QUERY)
        for query in ENSURE_PLAYER_INDEX_QUERIES:
            cursor.execute(query)
        conn.commit()
