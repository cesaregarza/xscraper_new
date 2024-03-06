import datetime as dt

import pytz
from splatnet3_scraper.query import QueryResponse

from xscraper import constants as xc
from xscraper.scraper.types import Player, Schedule
from xscraper.scraper.utils import base64_decode, color_floats_to_hex


def parse_player_data(data: QueryResponse) -> Player:
    badges = [
        int(base64_decode(badge["id"]).split("-")[-1]) if badge else None
        for badge in data["nameplate", "badges"]
    ]
    return Player(
        id=base64_decode(data["id"]).split(":")[-1],
        name=data["name"],
        name_id=data["nameId"],
        x_power=data["xPower"],
        weapon_id=int(base64_decode(data["weapon", "id"]).split("-")[-1]),
        nameplate_id=int(
            base64_decode(data["nameplate", "background", "id"]).split("-")[-1]
        ),
        badge_left_id=badges[0],
        badge_center_id=badges[1],
        badge_right_id=badges[2],
        byname=data["byname"],
        text_color=color_floats_to_hex(
            r=data["nameplate", "background", "textColor", "r"],
            g=data["nameplate", "background", "textColor", "g"],
            b=data["nameplate", "background", "textColor", "b"],
        ),
    )


def parse_players_in_mode(data: QueryResponse, mode: str) -> list[Player]:
    players = []
    for player_node in data["edges"]:
        player_data = parse_player_data(player_node["node"])
        player_data["mode"] = mode
        players.append(player_data)
    return players


def parse_time(time: str) -> dt.datetime:
    utc_tz = pytz.timezone("UTC")
    timestamp = dt.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
    return utc_tz.localize(timestamp)


def parse_schedule(data: QueryResponse) -> Schedule:
    responses = data[xc.schedule_path]
    schedule = []
    for response in responses:
        setting = response["xMatchSetting"]
        fest = setting is None
        base = Schedule(
            start_time=parse_time(response["startTime"]),
            end_time=parse_time(response["endTime"]),
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
