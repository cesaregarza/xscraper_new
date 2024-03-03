import base64
import datetime as dt
import glob
import json
import os
import pathlib
from typing import Any

import pytz
import sqlalchemy as db
from splatnet3_scraper.query import QueryHandler, QueryResponse
from sqlalchemy import Connection, create_engine
from sqlalchemy.dialects import postgresql as sql
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from xscraper.sql import Player as PlayerTable
from xscraper.sql import Schedule as ScheduleTable
from xscraper.types import Mode, ModeName, Player, Region, RegionName, Schedule


def base64_decode(string: str) -> str:
    return base64.b64decode(string).decode("utf-8")


class Connector:
    def __init__(self, session: Session):
        self.session = session

    @classmethod
    def from_url(cls, url: str) -> "Connector":
        engine = create_engine(url)
        session = Session(engine)
        return cls(session)

    @classmethod
    def from_connection(cls, connection: Connection) -> "Connector":
        session = Session(connection)
        return cls(session)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "Connector":
        url = (
            "postgresql+psycopg2://"
            f"{config['user']}:{config['password']}@"
            f"{config['host']}:{config['port']}/"
            f"{config['database']}"
        )
        return cls.from_url(url)

    def insert_schedule(self, schedule: Schedule) -> None:
        insert_statement = (
            sql.insert(ScheduleTable)
            .values(schedule)
            .on_conflict_do_nothing(index_elements=["start_time", "end_time"])
        )
        self.session.execute(insert_statement)

    def insert_player(self, player: Player) -> None:
        insert_statement = (
            sql.insert(PlayerTable)
            .values(player)
            .on_conflict_do_nothing(index_elements=["timestamp", "id", "mode"])
        )
        self.session.execute(insert_statement)

    def insert_schedules(self, schedules: list[Schedule]) -> None:
        try:
            for schedule in schedules:
                self.insert_schedule(schedule)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            raise e

    def insert_players(self, players: list[Player]) -> None:
        try:
            for player in players:
                self.insert_player(player)
            self.session.commit()
        except DBAPIError as e:
            self.session.rollback()
            raise e

    def get_latest_timestamp_and_mode(self) -> tuple:
        return (
            self.session.query(PlayerTable.timestamp, PlayerTable.mode)
            .order_by(PlayerTable.timestamp.desc())
            .first()
        )

    def get_current_schedule(self) -> Schedule:
        utc_tz = pytz.timezone("UTC")
        aware_now = utc_tz.localize(dt.datetime.utcnow())
        return (
            self.session.query(ScheduleTable)
            .filter(ScheduleTable.start_time <= aware_now)
            .filter(ScheduleTable.end_time > aware_now)
            .order_by(ScheduleTable.end_time.desc())
            .first()
        )

    def get_previous_schedule(self) -> Schedule:
        utc_tz = pytz.timezone("UTC")
        aware_now = utc_tz.localize(dt.datetime.utcnow())
        return (
            self.session.query(ScheduleTable)
            .filter(ScheduleTable.end_time <= aware_now)
            .order_by(ScheduleTable.end_time.desc())
            .first()
        )

    def ensure_schedule_table_exists(self) -> None:
        if not db.inspect(self.session.bind).has_table("schedule"):
            ScheduleTable.__table__.create(self.session.bind)

    def ensure_player_table_exists(self) -> None:
        if not db.inspect(self.session.bind).has_table("players"):
            PlayerTable.__table__.create(self.session.bind)


class S3InkReader:
    def __init__(self, glob_path: str):
        self.glob_path = glob_path

    def parse_player_path(self, path: str) -> tuple[dt.datetime, str, str]:
        filename = pathlib.Path(path).name
        parts = filename.split(".")
        date, time, _, _, region, rule, _ = parts
        datetime = dt.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H-%M-%S")
        return datetime, region, rule, path

    def get_player_paths(self) -> list[tuple[dt.datetime, str, str, str]]:
        paths = glob.glob(self.glob_path)
        paths = [self.parse_player_path(path) for path in paths]
        paths = sorted(paths, key=lambda x: x[0])
        return paths

    def read_player_path(path: str) -> QueryResponse:
        with open(path, "r") as f:
            return QueryResponse(json.load(f))

    def read_player_paths(self) -> list[QueryResponse]:
        return [self.read_player_path(path) for path in self.get_player_paths()]

    def read_schedule_path(self, path: str) -> QueryResponse:
        with open(path, "r") as f:
            return QueryResponse(json.load(f)["data"])

    def read_schedule_paths(self, glob_path: str) -> list[QueryResponse]:
        out = []
        for path in glob.glob(glob_path):
            try:
                out.append(self.read_schedule_path(path))
            except json.decoder.JSONDecodeError:
                pass
        return out


class XRankScraper:
    query = "XRankingQuery"
    schedule_query = "StageScheduleQuery"
    modes = ("Ar", "Cl", "Gl", "Lf")
    mode_map: dict[Mode, ModeName] = {
        "Ar": "Splat Zones",
        "Cl": "Clam Blitz",
        "Gl": "Rainmaker",
        "Lf": "Tower Control",
    }
    mode_reverse_map: dict[ModeName, Mode] = {
        "Splat Zones": "Ar",
        "Clam Blitz": "Cl",
        "Rainmaker": "Gl",
        "Tower Control": "Lf",
    }
    current_season_path = ("xRanking", "currentSeason", "id")
    detailed_x_query = "DetailTabViewXRanking%sRefetchQuery"
    detailed_weapon_query = "DetailTabViewWeaponTops%sRefetchQuery"
    regions = ("ATLANTIC", "PACIFIC")
    region_map: dict[Region, RegionName] = {
        "ATLANTIC": "Tentatek",
        "PACIFIC": "Takoroka",
    }
    schedule_path = ("xSchedules", "nodes")

    def __init__(self, scraper: QueryHandler, connector: Connector):
        self.scraper = scraper
        self.connector = connector
        utc_tz = pytz.timezone("UTC")
        timestamp = dt.datetime.utcnow()
        self.timestamp = utc_tz.localize(timestamp)

    @staticmethod
    def from_env() -> "XRankScraper":
        scraper = QueryHandler.from_config_file()
        connection_dict = {
            "host": os.environ["DB_HOST"],
            "port": os.environ["DB_PORT"],
            "user": os.environ["DB_USER"],
            "password": os.environ["DB_PASSWORD"],
            "database": os.environ["DB_DATABASE"],
        }
        connector = Connector.from_dict(connection_dict)
        return XRankScraper(scraper, connector)

    def update_timestamp(self) -> None:
        utc_tz = pytz.timezone("UTC")
        timestamp = dt.datetime.utcnow()
        self.timestamp = utc_tz.localize(timestamp)

    def end_cursor_path_x_rank(self, mode: str) -> str:
        return ("node", f"xRanking{mode}", "pageInfo", "endCursor")

    def get_current_season(self, region: Region) -> str:
        response = self.scraper.query(self.query, variables={"region": region})
        return response[self.current_season_path]

    def get_detailed_data(
        self,
        season_id: str,
        mode: Mode,
        page: int,
        cursor: str,
        weapons: bool = False,
    ) -> QueryResponse:
        variables = {
            "id": season_id,
            "mode": mode,
            "page": page,
            "cursor": cursor,
        }
        base_query = (
            self.detailed_weapon_query if weapons else self.detailed_x_query
        )
        detailed_query = base_query % mode
        response = self.scraper.query(detailed_query, variables=variables)
        return response

    def parse_player_data(self, data: QueryResponse) -> Player:
        return Player(
            id=base64_decode(data["id"]).split(":")[-1],
            name=data["name"],
            name_id=data["nameId"],
            rank=data["rank"],
            x_power=data["xPower"],
            weapon=data["weapon", "name"],
            weapon_id=data["weapon", "id"],
            weapon_sub=data["weapon", "subWeapon", "name"],
            weapon_sub_id=data["weapon", "subWeapon", "id"],
            weapon_special=data["weapon", "specialWeapon", "name"],
            weapon_special_id=data["weapon", "specialWeapon", "id"],
        )

    def parse_players_in_mode(
        self, data: QueryResponse, mode: str
    ) -> list[Player]:
        players = []
        for player_node in data["edges"]:
            player_data = self.parse_player_data(player_node["node"])
            player_data["mode"] = mode
            players.append(player_data)
        return players

    def scrape_all_players_in_region_and_mode(
        self, season_id: str, mode: str
    ) -> list[Player]:
        players = []
        for page in range(1, 6):
            has_next_page = True
            cursor = None
            while has_next_page:
                response = self.get_detailed_data(
                    season_id=season_id,
                    mode=mode,
                    page=page,
                    cursor=cursor,
                )
                subresponse = response["node", f"xRanking{mode}"]
                players.extend(self.parse_players_in_mode(subresponse, mode))

                has_next_page = subresponse["pageInfo", "hasNextPage"]
                cursor = subresponse["pageInfo", "endCursor"]
        return players

    def scrape_all_players_in_mode(
        self,
        mode: Mode,
        timestamp: dt.datetime | None = None,
    ) -> list[Player]:
        out = []
        timestamp_insert = timestamp or self.timestamp
        for region in self.regions:
            season_id = self.get_current_season(region=region)

            players = []
            players.extend(
                self.scrape_all_players_in_region_and_mode(season_id, mode)
            )
            for player in players:
                player["timestamp"] = timestamp_insert
                player["region"] = self.region_map[region]
                player["mode"] = self.mode_map[mode]
            out.extend(players)
        return out

    def parse_time(self, time: str) -> dt.datetime:
        utc_tz = pytz.timezone("UTC")
        timestamp = dt.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        return utc_tz.localize(timestamp)

    def get_schedule(
        self, response: QueryResponse | None = None
    ) -> list[Schedule]:
        if response is None:
            response = self.scraper.query(self.schedule_query)
        responses = response[self.schedule_path]
        schedule = []
        for response in responses:
            setting = response["xMatchSetting"]
            fest = setting is None
            base = Schedule(
                start_time=self.parse_time(response["startTime"]),
                end_time=self.parse_time(response["endTime"]),
                splatfest=fest,
            )
            if fest:
                schedule.append(base)
                continue

            base["mode"] = setting["vsRule", "name"]
            base["stage_1_id"] = setting["vsStages", 0, "vsStageId"]
            base["stage_1_name"] = setting["vsStages", 0, "name"]
            base["stage_2_id"] = setting["vsStages", 1, "vsStageId"]
            base["stage_2_name"] = setting["vsStages", 1, "name"]
            schedule.append(base)
        return schedule

    def update_schedule_db(self, response: QueryResponse | None = None) -> None:
        schedule = self.get_schedule(response=response)
        self.connector.ensure_schedule_table_exists()
        self.connector.insert_schedules(schedule)

    def calculate_modes_to_update(
        self, timestamp: dt.datetime
    ) -> list[Schedule]:
        current_mode = self.connector.get_current_schedule()

        if (timestamp.minute < 15) and (timestamp.hour % 2 == 0):
            previous_mode = self.connector.get_previous_schedule()
            return [
                previous_mode,
                current_mode,
            ]

        return [current_mode]

    def update_player_db(self) -> None:
        self.update_timestamp()
        players = []
        self.connector.ensure_player_table_exists()
        for schedule in self.calculate_modes_to_update(self.timestamp):
            mode = self.mode_reverse_map[schedule.mode]
            players_in_mode = self.scrape_all_players_in_mode(mode)
            for player in players_in_mode:
                player["rotation_start"] = schedule.start_time
            players.extend(players_in_mode)
        self.connector.insert_players(players)
