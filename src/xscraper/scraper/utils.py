import base64
import datetime as dt


def base64_decode(string: str) -> str:
    return base64.b64decode(string).decode("utf-8")


def color_floats_to_hex(r: float, g: float, b: float) -> str:
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def calculate_season_number(timestamp: dt.datetime) -> int:
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
