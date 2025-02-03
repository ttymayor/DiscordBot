from datetime import datetime, timedelta, timezone

def intensity_to_color(intensity, suffix):
    if intensity == 1:
        return 0xe0ffe0
    elif intensity == 2:
        return 0x33ff34
    elif intensity == 3:
        return 0xfffe2f
    elif intensity == 4:
        return 0xfe842e
    elif intensity == 5 and suffix == "弱":
        return 0xfe5231
    elif intensity == 5 and suffix == "強":
        return 0xc43c3c
    elif intensity == 6 and suffix == "弱":
        return 0x9a4644
    elif intensity == 6 and suffix == "強":
        return 0x9a4c86
    elif intensity == 7:
        return 0xb61eeb

def str_to_time(time_str):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

def time_to_stamp(time_str):
    tz = timezone(timedelta(hours=8))
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz).timestamp()
