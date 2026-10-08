"""UNIX Timestamp Rounder.

A focused, zero-dependency library for rounding datetime objects to the nearest
second, minute, or hour.

Design decision: rounding is anchored to the Unix epoch (1970-01-01T00:00:00Z).
This makes the operation a pure arithmetic shift on the timestamp value, so it
is timezone-agnostic and produces identical results regardless of the input
datetime's tzinfo. See ``round_datetime`` for the consequences.
"""

from .core import (
    HOUR,
    MINUTE,
    SECOND,
    HOUR_PRECISION,
    MINUTE_PRECISION,
    SECOND_PRECISION,
    Precision,
    Unit,
    round_datetime,
    round_timestamp,
)

__all__ = [
    "HOUR",
    "MINUTE",
    "SECOND",
    "HOUR_PRECISION",
    "MINUTE_PRECISION",
    "SECOND_PRECISION",
    "Precision",
    "Unit",
    "round_datetime",
    "round_timestamp",
]
