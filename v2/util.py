from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(ET)


def hm(s):
    h, m = s.split(":")
    return dtime(int(h), int(m))


def minute_index(ts):
    """Minutes since 9:30 ET (0 = first bar of the regular session)."""
    return ts.hour * 60 + ts.minute - (9 * 60 + 30)


def log(msg):
    print(f"[{datetime.now(ET):%H:%M:%S}] {msg}", flush=True)
