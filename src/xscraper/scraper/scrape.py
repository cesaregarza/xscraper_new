import datetime as dt

import pytz
from splatnet3_scraper.query import QueryHandler, QueryResponse

from xscraper import constants as xc
from xscraper.scraper.parse import (
    parse_players_in_mode,
    parse_schedule,
    parse_time,
)
from xscraper.scraper.types import Player, Schedule
from xscraper.scraper.utils import (
    base64_decode,
    calculate_season_number,
    color_floats_to_hex,
    pull_previous_schedule,
    round_down_nearest_rotation,
)
from xscraper.types import Mode, Region


def get_current_season(scraper: QueryHandler, region: Region) -> str:
    response = scraper.query(xc.query, variables={"region": region})
    return response[xc.current_season_path]


def pull_detailed_data(
    scraper: QueryHandler,
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
    base_query = xc.detailed_weapon_query if weapons else xc.detailed_x_query
    detailed_query = base_query % mode
    return scraper.query(detailed_query, variables=variables)


def scrape_all_players_in_region_and_mode(
    scraper: QueryHandler, season_id: str, mode: str
) -> list[Player]:
    players = []
    for page in range(1, 6):
        has_next_page = True
        cursor = None
        while has_next_page:
            response = pull_detailed_data(
                scraper=scraper,
                season_id=season_id,
                mode=mode,
                page=page,
                cursor=cursor,
            )
            subresponse = response["node", f"xRanking{mode}"]
            players.extend(parse_players_in_mode(subresponse, mode))
            has_next_page = subresponse["pageInfo", "hasNextPage"]
            cursor = subresponse["pageInfo", "endCursor"]
    return players


def scrape_all_players_in_mode(
    scraper: QueryHandler,
    mode: Mode,
    timestamp: dt.datetime | None = None,
) -> list[Player]:
    out = []
    if timestamp:
        timestamp_insert = timestamp
    else:
        utc_tz = pytz.timezone("UTC")
        timestamp_insert = dt.datetime.now(utc_tz)

    season_number = calculate_season_number(timestamp_insert)
    for region in xc.regions:
        season_id = get_current_season(scraper, region)

        players = []
        players.extend(
            scrape_all_players_in_region_and_mode(scraper, season_id, mode)
        )
        for player in players:
            player["timestamp"] = timestamp_insert
            player["region"] = xc.region_map[region]
            player["mode"] = xc.mode_map[mode]
            player["season_number"] = season_number

        out.extend(players)
    return out


def get_schedule(scraper: QueryHandler) -> list[Schedule]:
    response = scraper.query(xc.schedule_query)
    return parse_schedule(response)
