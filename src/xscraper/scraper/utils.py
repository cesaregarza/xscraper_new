import base64


def base64_decode(string: str) -> str:
    return base64.b64decode(string).decode("utf-8")


def color_floats_to_hex(r: float, g: float, b: float) -> str:
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
