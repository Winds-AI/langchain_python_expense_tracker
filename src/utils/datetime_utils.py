"""
Timezone & datetime parsing helpers for IST handling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")


def now_ist_iso() -> str:
    """Return the current time in IST as ISO8601 string."""
    return datetime.now(tz=IST).isoformat()


def to_ist(dt: datetime) -> datetime:
    """Convert any datetime to IST. If naive, assume UTC before converting."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)


def to_utc(dt: datetime, assume_tz: ZoneInfo = IST) -> datetime:
    """Convert any datetime to UTC. If naive, assume provided timezone (default IST)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=assume_tz)
    return dt.astimezone(UTC)


def parse_to_utc(value: Union[str, datetime], default_tz: ZoneInfo = IST) -> datetime:
    """Parse model output datetime into UTC.

    - If `value` is ISO string, parse it; if naive, assume `default_tz`.
    - If `value` is datetime, if naive assume `default_tz`.
    - Return timezone-aware UTC datetime.
    """
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except Exception:
            # Fallback to now if parsing fails
            parsed = datetime.now(tz=default_tz)
    elif isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.now(tz=default_tz)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=default_tz)
    return parsed.astimezone(UTC)

