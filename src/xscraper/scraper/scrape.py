from splatnet3_scraper.query import QueryHandler, QueryResponse

from xscraper.scraper.types import Player
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
