"""
Maps publication timestamps to the trading day whose close they precede, so sentiment never
leaks into a bar before it was knowable.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

MARKET_TZ = ZoneInfo("America/New_York")
MARKET_CLOSE = time(16, 0)


def is_trading_day(day: date) -> bool:
    """
    Approximates the NYSE calendar with weekdays.
    TODO: exclude NYSE holidays (e.g. via pandas_market_calendars) once a real source lands.
    """

    return day.weekday() < 5


def next_trading_day(day: date) -> date:
    """
    :returns: The first trading day strictly after "day"
    """

    day += timedelta(days=1)
    while not is_trading_day(day):
        day += timedelta(days=1)
    return day


def as_of_trading_date(published_at: datetime) -> date:
    """
    The trading day an item counts toward. Items published before 16:00 New York time on a
    trading day count for that day; anything later, or on a non-trading day, rolls forward
    to the next trading day.

    :param published_at: Publication time. Must be timezone-aware (UTC recommended)
    :returns: Trading date the item is "known by the close" of
    """

    if published_at.tzinfo is None:
        raise ValueError("published_at must be timezone-aware; pass UTC timestamps")

    local = published_at.astimezone(MARKET_TZ)
    day = local.date()

    if is_trading_day(day) and local.time() < MARKET_CLOSE:
        return day
    return next_trading_day(day)
