import os

import psycopg2
from psycopg2.extras import execute_values

from xscraper.scraper.sql import INSERT_PLAYER_QUERY
from xscraper.scraper.types import Player, Schedule


def get_db_credentials() -> dict[str, str]:
    return {
        "dbname": os.getenv("POSTGRES_NAME"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
    }


def get_db_connection() -> psycopg2.extensions.connection:
    return psycopg2.connect(**get_db_credentials())


def insert_players(players: list[Player]) -> None:
    with get_db_connection() as conn:
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
