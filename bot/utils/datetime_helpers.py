from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from ..config import settings

_TZ = ZoneInfo(getattr(settings, "tz", "Europe/Moscow"))

DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def now_local() -> datetime:
    return datetime.now(tz=_TZ)


def is_valid_date(value: str) -> bool:
    return bool(DATE_RE.match(value))


def is_valid_time(value: str) -> bool:
    return bool(TIME_RE.match(value))
