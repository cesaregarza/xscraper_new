from xscraper.types import Mode, ModeName

# Query Constants
query = "XRankingQuery"
schedule_query = "StageScheduleQuery"
detailed_x_query = "DetailTabViewXRanking%sRefetchQuery"
detailed_weapon_query = "DetailTabViewWeaponTops%sRefetchQuery"

# Mode Constants
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

# Season Constants
current_season_path = ("xRanking", "currentSeason", "id")

# Region Constants
regions = ("ATLANTIC", "PACIFIC")
region_map = {
    "ATLANTIC": "Tentatek",
    "PACIFIC": "Takoroka",
}
region_map_bool = {
    "ATLANTIC": False,
    "PACIFIC": True,
}

# Schedule Constants
schedule_path = ("xSchedules", "nodes")
