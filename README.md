# UNIX Timestamp Rounder

Rounds `datetime` objects or raw POSIX timestamps to the nearest second, minute, or hour, with zero third-party dependencies.

```python
from datetime import datetime, timezone
from unix_timestamp_rounder import (
    round_datetime,
    round_timestamp,
    SECOND_PRECISION,
    MINUTE_PRECISION,
    HOUR_PRECISION,
)

round_datetime(
    datetime(2021, 6, 15, 12, 0, 0, 250_000, tzinfo=timezone.utc),
    SECOND_PRECISION,
)
# -> datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

round_timestamp(30.0, MINUTE_PRECISION)
# -> 60.0
```

## Why this exists

The standard library exposes no built-in for rounding datetimes to a coarser resolution. The natural way to do it is to work in Unix-timestamp space — seconds since the epoch — because there rounding is a single `floor(ts / precision + 0.5)` arithmetic shift with no calendar lookups. This library is that idea, distilled to two functions: `round_timestamp(ts, precision)` for the numeric case and `round_datetime(dt, precision=..., tz=...)` for the datetime case.

The trade-off: rounding is anchored to the epoch, not to the wall clock of the input's timezone. For UTC and naive inputs (treated as UTC) the result is always what a human expects. For a timezone with DST, the rounded wall-clock value during the transition hour can look off-by-one, because the rounding snapped a float to a multiple of `precision` seconds from `1970-01-01T00:00:00Z`, not from the local midnight. This is the standard behaviour of every timestamp-rounding utility; it is documented here so it does not surprise you.

## Edge cases you will hit

- **Half intervals round up.** `30.0` seconds rounds to `60.0` under minute precision, not to `0.0`. This is round-half-up, applied consistently including for negative timestamps (`-1.5` rounds to `-1.0`).
- **Naive datetimes are treated as UTC**, not as local time, so results are reproducible across machines with different `TZ` settings. The returned datetime is always timezone-aware; call `.replace(tzinfo=None)` if you need a naive value.
- **`precision` must be strictly positive.** Passing zero or a negative value raises `ValueError`.
- **Sub-second precision is supported.** `round_timestamp(0.3, 0.5)` returns `0.5`. The exported `SECOND_PRECISION`, `MINUTE_PRECISION`, and `HOUR_PRECISION` constants cover the common cases.

## Exported names

- `round_timestamp(ts: float, precision: Precision) -> float`
- `round_datetime(dt: datetime, precision: Precision = SECOND_PRECISION, tz: tzinfo = timezone.utc) -> datetime`
- `SECOND_PRECISION`, `MINUTE_PRECISION`, `HOUR_PRECISION` — canonical `Precision` shorthands (1, 60, 3600 seconds).
- `SECOND`, `MINUTE`, `HOUR` — integer-second `Unit` constants.
- `Precision` — type alias for `Union[int, float]`.
- `Unit` — type alias for `int`.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

