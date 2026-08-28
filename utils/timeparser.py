async def parse_time_to_seconds(value: str) -> float:
    value = str(value).strip()

    if value.replace(".", "", 1).isdigit():
        return float(value)

    if "." in value:
        time_part, ms_part = value.split(".", 1)
        if not ms_part.isdigit() or len(ms_part) > 3:
            raise ValueError(f"Invalid milliseconds in time: {value}")
        ms = int(ms_part.ljust(3, "0")) 
    else:
        time_part = value
        ms = 0

    parts = time_part.split(":")

    try:
        if len(parts) == 3:  # HH:MM:SS
            h, m, s = map(int, parts)
        elif len(parts) == 2:  # MM:SS
            h = 0
            m, s = map(int, parts)
        elif len(parts) == 1:  # SS
            h = 0
            m = 0
            s = int(parts[0])
        else:
            raise ValueError
    except ValueError:
        raise ValueError(f"Invalid time format: {value}")

    if not (0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"Invalid time range: {value}")

    return h * 3600 + m * 60 + s + ms / 1000

async def parse_seconds_to_time(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("Time cannot be negative")

    total_ms = round(seconds * 1000)
    s, ms = divmod(total_ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    parts = []

    if h > 0:
        parts.append(f"{h:02d}")
        parts.append(f"{m:02d}")
    else:
        parts.append(f"{m:02d}" if m > 0 else "0")

    parts.append(f"{s:02d}")

    time_str = ":".join(parts)

    if ms > 0:
        time_str += f".{ms:03d}"

    return time_str