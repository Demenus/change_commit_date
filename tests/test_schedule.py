from datetime import datetime, timedelta, timezone
import unittest

from ccd.schedule import DailyWindow, WindowError, plan_dates


UTC = timezone.utc


def at(day, hour, minute=0, second=0):
    return datetime(2024, 1, day, hour, minute, second, tzinfo=UTC)


class DailyWindowTests(unittest.TestCase):
    def test_parses_normal_and_overnight_windows(self):
        self.assertFalse(DailyWindow.parse("09:00-17:00").crosses_midnight)
        self.assertTrue(DailyWindow.parse("18:00-03:00").crosses_midnight)

    def test_rejects_invalid_windows(self):
        with self.assertRaises(WindowError):
            DailyWindow.parse("18:00")
        with self.assertRaises(WindowError):
            DailyWindow.parse("18:00-18:00")

    def test_overnight_window_contains_both_sides_of_midnight(self):
        window = DailyWindow.parse("18:00-03:00")
        self.assertTrue(window.contains(at(1, 18)))
        self.assertTrue(window.contains(at(2, 2, 59)))
        self.assertFalse(window.contains(at(2, 3)))
        self.assertFalse(window.contains(at(1, 12)))

    def test_first_anchor_preserves_minute_and_second(self):
        plan = plan_dates([("a", at(1, 10, 12, 34))], DailyWindow.parse("18:00-03:00"))
        self.assertEqual(plan[0].planned, at(1, 18, 12, 34))

    def test_preserves_interval_while_candidate_is_open(self):
        plan = plan_dates(
            [("a", at(1, 10, 12)), ("b", at(1, 12, 32))],
            DailyWindow.parse("18:00-03:00"),
        )
        self.assertEqual(plan[1].planned - plan[0].planned, timedelta(hours=2, minutes=20))
        self.assertEqual(plan[1].planned, at(1, 20, 32))

    def test_moves_to_next_opening_after_closed_period(self):
        plan = plan_dates(
            [("a", at(1, 1)), ("b", at(1, 5))], DailyWindow.parse("18:00-03:00")
        )
        self.assertEqual(plan[0].planned, at(1, 1))
        self.assertEqual(plan[1].planned, at(1, 18))

    def test_keeps_valid_commits_after_an_adjustment(self):
        plan = plan_dates(
            [
                ("first", at(17, 11, 53, 42)),
                ("adjusted", at(19, 10, 15)),
                ("valid", at(19, 18, 29, 53)),
                ("also-valid", at(19, 18, 54, 24)),
                ("last", at(20, 16, 35, 43)),
            ],
            DailyWindow.parse("18:00-03:00"),
        )
        self.assertEqual(plan[0].planned, at(17, 18, 53, 42))
        self.assertEqual(plan[1].planned, at(19, 18))
        self.assertEqual(plan[2].planned, at(19, 18, 29, 53))
        self.assertEqual(plan[3].planned, at(19, 18, 54, 24))
        self.assertEqual(plan[4].planned, at(20, 18))

    def test_keeps_timezone_offset(self):
        offset = timezone(timedelta(hours=5, minutes=30))
        original = datetime(2024, 1, 1, 10, 12, tzinfo=offset)
        planned = plan_dates([("a", original)], DailyWindow.parse("18:00-03:00"))[0]
        self.assertEqual(planned.planned.utcoffset(), timedelta(hours=5, minutes=30))
        self.assertEqual(planned.planned.hour, 18)
