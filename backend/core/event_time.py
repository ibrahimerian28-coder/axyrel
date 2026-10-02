"""Owner-approved event-time policy (OD-14) for Schedule and Service Visit events."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


CAIRO = ZoneInfo("Africa/Cairo")


def normalize_event_time(value: datetime) -> datetime:
    """Resolve an explicit offset or an unambiguous Cairo wall clock to UTC."""
    if value.utcoffset() is not None:
        return value.astimezone(timezone.utc)

    candidates = set()
    for fold in (0, 1):
        instant = value.replace(tzinfo=CAIRO, fold=fold).astimezone(timezone.utc)
        if instant.astimezone(CAIRO).replace(tzinfo=None) == value:
            candidates.add(instant)
    if len(candidates) != 1:
        raise ValueError("Ambiguous or nonexistent Africa/Cairo time; supply an explicit UTC offset.")
    return candidates.pop()
