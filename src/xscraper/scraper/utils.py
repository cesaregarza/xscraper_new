import base64
import datetime as dt

import pytz


def base64_decode(string: str) -> str:
    """Decode a base64 string and return the result as a utf-8 string.

    Args:
        string (str): A base64 encoded string.

    Returns:
        str: The decoded string.
    """
    return base64.b64decode(string).decode("utf-8")


def color_floats_to_hex(r: float, g: float, b: float) -> str:
    """Convert RGB floats to a hex color string.

    Args:
        r (float): red value
        g (float): green value
        b (float): blue value

    Returns:
        str: The hex color string, formatted as "#RRGGBB".
    """
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def calculate_season_number(timestamp: dt.datetime) -> int:
    """Calculate the season number based on the timestamp. The first season is
    Winter 2022, which is December 2022 to February 2023.

    Args:
        timestamp (dt.datetime): The timestamp to calculate the season number
        for.

    Returns:
        int: The season number.
    """
    # First season is Winter 2022, which is December 2022 to February 2023
    year = 4 * (timestamp.year - 2022)
    if timestamp.month < 3:
        year -= 4

    month = timestamp.month
    offset = 0
    if month in (12, 1, 2):
        offset = 0
    elif month in (3, 4, 5):
        offset = -3
    elif month in (6, 7, 8):
        offset = -2
    elif month in (9, 10, 11):
        offset = -1

    return year + offset + 1


def pull_previous_schedule(timestamp: dt.datetime) -> bool:
    """Check if the timestamp should also pull the previous schedule.

    Args:
        timestamp (dt.datetime): The timestamp to check.

    Returns:
        bool: True if the timestamp is before 15 minutes into an even hour.
    """
    return (timestamp.minute < 15) and (timestamp.hour % 2 == 0)


def round_down_nearest_rotation(timestamp: dt.datetime) -> dt.datetime:
    """Round down the timestamp to the nearest rotation start time.

    Args:
        timestamp (dt.datetime): The timestamp to round down.

    Returns:
        dt.datetime: The rounded down timestamp.
    """
    return timestamp.replace(
        hour=timestamp.hour // 2 * 2, minute=0, second=0, microsecond=0
    )


def get_current_rotation_start(previous: bool = False) -> dt.datetime:
    """Get the current rotation start time in UTC.

    Args:
        previous (bool): If True, return the previous rotation start time.
        Defaults to False.

    Returns:
        dt.datetime: The current rotation start time.
    """
    utc_tz = pytz.timezone("UTC")
    timestamp = dt.datetime.now(utc_tz)
    out = round_down_nearest_rotation(timestamp)
    if previous:
        out -= dt.timedelta(hours=2)
    return out
