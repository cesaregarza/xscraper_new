import datetime as dt
from typing import Literal, NotRequired, TypeAlias, TypedDict

Region: TypeAlias = Literal["ATLANTIC", "PACIFIC"]
RegionName: TypeAlias = Literal["Tentatek", "Takoroka"]
Mode: TypeAlias = Literal["Ar", "Cl", "Gl", "Lf"]
ModeName: TypeAlias = Literal[
    "Splat Zones", "Clam Blitz", "Rainmaker", "Tower Control"
]


class Player(TypedDict):
    id: str
    name: str
    name_id: str
    rank: int
    x_power: float
    weapon_id: int
    nameplate_id: int
    byname: str
    text_color: str
    badge_left_id: NotRequired[str]
    badge_center_id: NotRequired[str]
    badge_right_id: NotRequired[str]
    timestamp: NotRequired[dt.datetime]
    mode: NotRequired[ModeName]
    region: NotRequired[RegionName]
    rotation_start: NotRequired[dt.datetime]
    season_number: NotRequired[int]


class Schedule(TypedDict):
    start_time: dt.datetime
    end_time: dt.datetime
    splatfest: bool
    mode: NotRequired[ModeName]
    stage_1_id: NotRequired[int]
    stage_1_name: NotRequired[str]
    stage_2_id: NotRequired[int]
    stage_2_name: NotRequired[str]
