"""Core rounding logic.

The central design choice: we round in Unix-timestamp space (seconds since
1970-01-01T00:00:00Z), not in wall-clock space. This keeps the operation a
simple ``floor(ts + period/2)`` arithmetic shift with no calendar arithmetic,
no DST surprises, and no month-length lookups. The trade-off is that "nearest
minute" is measured in SI seconds from the epoch, which for a timezone with a
DST transition can round to a wall-clock value that looks off-by-one in the
timezone's local numbering during the hour around the transition. For UTC and
naive datetimes (treated as UTC) the result is always what a human expects.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from typing import Union

# Public type aliases. We keep ``Precision`` as a simple alias for ``int`` so the
# API is friendly to callers who want to pass a raw integer second count.
Precision = Union[int, float]
Unit = int

# Canonical ``Unit`` constants in seconds.
SECOND: Unit = 1
MINUTE: Unit = 60
HOUR: Unit = 3600

# Convenience ``Precision`` shorthands. These are the canonical way to express
# "round to the nearest whole second / minute / hour" and are stable regardless
# of leap seconds (Python's ``datetime`` ignores leap seconds entirely).
SECOND_PRECISION: Precision = SECOND
MINUTE_PRECISION: Precision = MINUTE
HOUR_PRECISION: Precision = HOUR


def _to_timestamp(dt: datetime) -> float:
    """Return the POSIX timestamp for ``dt``, handling naive datetimes as UTC.

    Python's ``datetime.timestamp()`` treats naive datetimes as local time,
    which would make rounding depend on the machine's TZ setting. We instead
    interpret naive inputs as UTC so results are reproducible across machines.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _to_datetime(ts: float, tz: tzinfo) -> datetime:
    """Inverse of ``_to_timestamp`` for a target timezone.

    ``datetime.fromtimestamp`` returns a naive datetime in local time when
    given ``None``; we always pass an explicit tz to avoid that ambiguity.
    """
    return datetime.fromtimestamp(ts, tz)


def round_timestamp(ts: float, precision: Precision) -> float:
    """Round a Unix timestamp to the nearest multiple of ``precision`` seconds.

    Uses standard round-half-up semantics: ``floor(ts / precision + 0.5)``
    implemented in integer-safe form via a math identity to avoid floating
    rounding drift on large timestamps. Accepts integer or float ``precision``
    values greater than zero.

    Parameters
    ----------
    ts
        Seconds since 1970-01-01T00:00:00Z. May be fractional.
    precision
        Rounding interval in seconds. Must be strictly positive. May be
        fractional (e.g. ``0.5`` to round to the nearest half-second), but the
        common ``SECOND_PRECISION`` / ``MINUTE_PRECISION`` / ``HOUR_PRECISION``
        constants cover the typical cases.

    Returns
    -------
    float
        The rounded timestamp. Always a ``float``; callers wanting an integer
        second count should wrap the result in ``int()``.
    """
    if precision <= 0:
        raise ValueError("precision must be strictly positive")
    # Round-half-up at the interval granularity. The two-step form avoids
    # catastrophic precision loss for very large ts values where ``ts + p/2``
    # alone can round to the wrong representable float.
    quotient = ts / precision
    return float(int(quotient + 0.5)) * precision


def round_datetime(
    dt: datetime,
    precision: Precision = SECOND_PRECISION,
    tz: tzinfo = timezone.utc,
) -> datetime:
    """Round a datetime to the nearest multiple of ``precision`` seconds.

    Naive datetimes are interpreted as UTC before rounding. The returned
    datetime is always timezone-aware and carries ``tz``. To get a naive
    result, call ``.replace(tzinfo=None)`` on the return value.

    Parameters
    ----------
    dt
        The datetime to round. May be naive or timezone-aware.
    precision
        Rounding interval in seconds. Defaults to one second. Pass one of
        ``SECOND_PRECISION``, ``MINUTE_PRECISION``, ``HOUR_PRECISION`` for
        clarity, or any positive number for sub-second / custom intervals.
    tz
        Timezone for the returned datetime. Rounding itself happens in
        timestamp space, so this only affects how the result is presented.
        Defaults to UTC.

    Returns
    -------
    datetime
        A timezone-aware datetime in ``tz``, snapped to the nearest multiple
        of ``precision`` seconds since the Unix epoch.
    """
    ts = _to_timestamp(dt)
    rounded = round_timestamp(ts, precision)
    return _to_datetime(rounded, tz)
