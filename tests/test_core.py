import unittest
from datetime import datetime, timedelta, timezone

from unix_timestamp_rounder import (
    HOUR,
    MINUTE,
    SECOND,
    HOUR_PRECISION,
    MINUTE_PRECISION,
    SECOND_PRECISION,
    round_datetime,
    round_timestamp,
)


class TestRoundTimestamp(unittest.TestCase):
    def test_rounds_to_nearest_second_exact(self):
        self.assertEqual(round_timestamp(0.0, SECOND_PRECISION), 0.0)
        self.assertEqual(round_timestamp(1.0, SECOND_PRECISION), 1.0)

    def test_rounds_half_second_up(self):
        # 0.5 -> nearest whole second is 1.0 (round-half-up).
        self.assertEqual(round_timestamp(0.5, SECOND_PRECISION), 1.0)
        self.assertEqual(round_timestamp(1.5, SECOND_PRECISION), 2.0)

    def test_rounds_sub_second_below_half_down(self):
        self.assertEqual(round_timestamp(0.4, SECOND_PRECISION), 0.0)
        self.assertEqual(round_timestamp(0.6, SECOND_PRECISION), 1.0)

    def test_minute_precision(self):
        # 30s is exactly half a minute -> rounds up to 60s.
        self.assertEqual(round_timestamp(30.0, MINUTE_PRECISION), 60.0)
        self.assertEqual(round_timestamp(29.0, MINUTE_PRECISION), 0.0)
        self.assertEqual(round_timestamp(31.0, MINUTE_PRECISION), 60.0)
        self.assertEqual(round_timestamp(119.0, MINUTE_PRECISION), 120.0)

    def test_hour_precision(self):
        # 1800s is exactly half an hour (3600/2) -> rounds up to 3600.
        self.assertEqual(round_timestamp(1800.0, HOUR_PRECISION), 3600.0)
        self.assertEqual(round_timestamp(1799.0, HOUR_PRECISION), 0.0)
        self.assertEqual(round_timestamp(1801.0, HOUR_PRECISION), 3600.0)

    def test_negative_timestamp_half(self):
        # -0.5 -> round-half-up toward +inf means -0.5 -> 0.0.
        self.assertEqual(round_timestamp(-0.5, SECOND_PRECISION), 0.0)
        # -1.5 -> -1.0
        self.assertEqual(round_timestamp(-1.5, SECOND_PRECISION), -1.0)

    def test_fractional_precision(self):
        # Round to nearest 0.5 seconds.
        self.assertEqual(round_timestamp(0.2, 0.5), 0.0)
        self.assertEqual(round_timestamp(0.3, 0.5), 0.5)
        self.assertEqual(round_timestamp(0.7, 0.5), 0.5)
        self.assertEqual(round_timestamp(0.8, 0.5), 1.0)

    def test_invalid_precision(self):
        for bad in (0, -1, -0.5):
            with self.assertRaises(ValueError):
                round_timestamp(100.0, bad)

    def test_large_timestamp_stable(self):
        # A timestamp well into the year 2100. The two-step quotient form
        # must not lose enough precision to round to a neighbouring second.
        ts = 4102444800.0  # 2100-01-01T00:00:00Z
        self.assertEqual(round_timestamp(ts, SECOND_PRECISION), ts)
        self.assertEqual(round_timestamp(ts + 0.6, SECOND_PRECISION), ts + 1.0)
        self.assertEqual(round_timestamp(ts + 0.4, SECOND_PRECISION), ts)

    def test_constants(self):
        self.assertEqual(SECOND, 1)
        self.assertEqual(MINUTE, 60)
        self.assertEqual(HOUR, 3600)
        self.assertEqual(SECOND_PRECISION, SECOND)
        self.assertEqual(MINUTE_PRECISION, MINUTE)
        self.assertEqual(HOUR_PRECISION, HOUR)


class TestRoundDatetime(unittest.TestCase):
    def test_round_naive_treated_as_utc(self):
        dt = datetime(1970, 1, 1, 0, 0, 0, 500_000)  # +0.5s
        rounded = round_datetime(dt)
        self.assertEqual(rounded, datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc))

    def test_round_aware_utc(self):
        dt = datetime(1970, 1, 1, 0, 0, 0, 400_000, tzinfo=timezone.utc)
        rounded = round_datetime(dt)
        self.assertEqual(rounded, datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc))

    def test_minute_precision_datetime(self):
        # 00:00:30 -> rounds up to 00:01:00
        dt = datetime(1970, 1, 1, 0, 0, 30, tzinfo=timezone.utc)
        rounded = round_datetime(dt, MINUTE_PRECISION)
        self.assertEqual(rounded, datetime(1970, 1, 1, 0, 1, 0, tzinfo=timezone.utc))

    def test_hour_precision_datetime(self):
        # 00:30:00 -> rounds up to 01:00:00
        dt = datetime(1970, 1, 1, 0, 30, 0, tzinfo=timezone.utc)
        rounded = round_datetime(dt, HOUR_PRECISION)
        self.assertEqual(rounded, datetime(1970, 1, 1, 1, 0, 0, tzinfo=timezone.utc))

    def test_custom_timezone_returned(self):
        tz = timezone(timedelta(hours=5, minutes=30))  # IST
        dt = datetime(1970, 1, 1, 6, 0, 30, tzinfo=tz)
        # 6:00:30 IST == 00:30:30 UTC == 1820.5 seconds since epoch.
        # Rounded to nearest minute: 00:31:00 UTC == 1820.0? No: 1820.5
        # rounds to 1860.0 (00:31:00 UTC). In IST that is 06:01:00.
        rounded = round_datetime(dt, MINUTE_PRECISION, tz=tz)
        self.assertEqual(
            rounded,
            datetime(1970, 1, 1, 6, 1, 0, tzinfo=tz),
        )

    def test_naive_input_returns_aware(self):
        dt = datetime(2021, 6, 15, 12, 0, 0, 250_000)
        rounded = round_datetime(dt)
        self.assertIsNotNone(rounded.tzinfo)
        self.assertEqual(rounded.tzinfo, timezone.utc)

    def test_round_trip_subsecond(self):
        # 0.25 -> 0.0, 0.75 -> 1.0
        dt = datetime(1970, 1, 1, 0, 0, 0, 250_000, tzinfo=timezone.utc)
        self.assertEqual(
            round_datetime(dt),
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        dt2 = datetime(1970, 1, 1, 0, 0, 0, 750_000, tzinfo=timezone.utc)
        self.assertEqual(
            round_datetime(dt2),
            datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        )

    def test_naive_minute_precision(self):
        dt = datetime(1970, 1, 1, 0, 0, 29)
        self.assertEqual(
            round_datetime(dt, MINUTE_PRECISION),
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
