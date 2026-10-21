import datetime
import unittest

from business_days_utils import BusinessDayCalendar, count_business_days, add_business_days


class TestIsBusinessDay(unittest.TestCase):
    def test_plain_monday(self):
        cal = BusinessDayCalendar()
        monday = datetime.date(2024, 1, 8)  # second Monday of January 2024
        self.assertTrue(cal.is_business_day(monday))

    def test_saturday_is_not_business_day(self):
        cal = BusinessDayCalendar()
        saturday = datetime.date(2024, 1, 6)
        self.assertFalse(cal.is_business_day(saturday))

    def test_sunday_is_not_business_day(self):
        cal = BusinessDayCalendar()
        sunday = datetime.date(2024, 1, 7)
        self.assertFalse(cal.is_business_day(sunday))

    def test_holiday_is_not_business_day(self):
        new_year = datetime.date(2024, 1, 1)
        cal = BusinessDayCalendar([new_year])
        self.assertFalse(cal.is_business_day(new_year))

    def test_holiday_on_weekend_still_excluded(self):
        # 2024-01-06 is a Saturday; listing it as a holiday is redundant
        # but must not raise or accidentally make it a business day.
        sat = datetime.date(2024, 1, 6)
        cal = BusinessDayCalendar([sat])
        self.assertFalse(cal.is_business_day(sat))


class TestCountBusinessDays(unittest.TestCase):
    def test_zero_when_equal(self):
        cal = BusinessDayCalendar()
        d = datetime.date(2024, 1, 8)
        self.assertEqual(cal.count_business_days(d, d), 0)

    def test_single_weekday(self):
        cal = BusinessDayCalendar()
        self.assertEqual(
            cal.count_business_days(datetime.date(2024, 1, 8),
                                    datetime.date(2024, 1, 9)),
            1,
        )

    def test_full_week_mon_to_mon(self):
        # Monday to next Monday = 5 business days (half-open end)
        cal = BusinessDayCalendar()
        self.assertEqual(
            cal.count_business_days(datetime.date(2024, 1, 8),
                                    datetime.date(2024, 1, 15)),
            5,
        )

    def test_skips_holiday_inside_range(self):
        # 2024-01-15 is MLK day; treat it as a holiday and verify it is
        # not counted.
        mlk = datetime.date(2024, 1, 15)
        cal = BusinessDayCalendar([mlk])
        # 2024-01-08 (Mon) to 2024-01-16 (Tue) = Mon,Tue,Wed,Thu,Fri,
        # then Mon 15th is a holiday (excluded), Tue 16th is the excluded
        # end. So 5 business days.
        self.assertEqual(
            cal.count_business_days(datetime.date(2024, 1, 8),
                                    datetime.date(2024, 1, 16)),
            5,
        )

    def test_reversed_dates_return_negative(self):
        cal = BusinessDayCalendar()
        self.assertEqual(
            cal.count_business_days(datetime.date(2024, 1, 9),
                                    datetime.date(2024, 1, 8)),
            -1,
        )

    def test_range_starting_on_weekend(self):
        # Saturday 2024-01-06 to Monday 2024-01-08 — the Saturday is not
        # counted, the Sunday is not counted, Monday is the end (excluded).
        cal = BusinessDayCalendar()
        self.assertEqual(
            cal.count_business_days(datetime.date(2024, 1, 6),
                                    datetime.date(2024, 1, 8)),
            0,
        )

    def test_range_ending_on_weekend(self):
        # Friday 2024-01-12 to Monday 2024-01-15 — Friday counts, weekend
        # days do not, Monday is the excluded end.
        cal = BusinessDayCalendar()
        self.assertEqual(
            cal.count_business_days(datetime.date(2024, 1, 12),
                                    datetime.date(2024, 1, 15)),
            1,
        )


class TestAddBusinessDays(unittest.TestCase):
    def test_add_zero_on_business_day_returns_same(self):
        cal = BusinessDayCalendar()
        monday = datetime.date(2024, 1, 8)
        self.assertEqual(cal.add_business_days(monday, 0), monday)

    def test_add_zero_on_weekend_rolls_forward(self):
        cal = BusinessDayCalendar()
        saturday = datetime.date(2024, 1, 6)
        self.assertEqual(cal.add_business_days(saturday, 0),
                         datetime.date(2024, 1, 8))

    def test_add_one_to_monday_returns_tuesday(self):
        cal = BusinessDayCalendar()
        self.assertEqual(
            cal.add_business_days(datetime.date(2024, 1, 8), 1),
            datetime.date(2024, 1, 9),
        )

    def test_add_one_on_friday_skips_weekend(self):
        cal = BusinessDayCalendar()
        friday = datetime.date(2024, 1, 12)
        self.assertEqual(cal.add_business_days(friday, 1),
                         datetime.date(2024, 1, 15))

    def test_add_five_business_days_crosses_weekend(self):
        cal = BusinessDayCalendar()
        monday = datetime.date(2024, 1, 8)
        # 5 business days forward from Monday is next Monday
        self.assertEqual(cal.add_business_days(monday, 5),
                         datetime.date(2024, 1, 15))

    def test_add_negative_one_from_monday_returns_previous_friday(self):
        cal = BusinessDayCalendar()
        monday = datetime.date(2024, 1, 8)
        self.assertEqual(cal.add_business_days(monday, -1),
                         datetime.date(2024, 1, 5))

    def test_add_negative_one_from_weekend_rolls_back(self):
        cal = BusinessDayCalendar()
        sunday = datetime.date(2024, 1, 7)
        # Sunday rolls back to Friday (previous business day) without
        # consuming a unit, then advances -1 more to Thursday.
        self.assertEqual(cal.add_business_days(sunday, -1),
                         datetime.date(2024, 1, 4))

    def test_add_skips_holiday(self):
        mlk = datetime.date(2024, 1, 15)
        cal = BusinessDayCalendar([mlk])
        # Friday 2024-01-12 + 1 business day would normally be Monday
        # 2024-01-15, but that is a holiday, so we land on Tuesday.
        self.assertEqual(
            cal.add_business_days(datetime.date(2024, 1, 12), 1),
            datetime.date(2024, 1, 16),
        )

    def test_add_starting_on_holiday_rolls_forward(self):
        mlk = datetime.date(2024, 1, 15)
        cal = BusinessDayCalendar([mlk])
        # Starting on the holiday with n=1 should roll to the next business
        # day (Tuesday 16th) and THEN advance one more (Wednesday 17th).
        self.assertEqual(
            cal.add_business_days(mlk, 1),
            datetime.date(2024, 1, 17),
        )


class TestModuleLevelFunctions(unittest.TestCase):
    def test_module_count_matches_class(self):
        cal = BusinessDayCalendar()
        self.assertEqual(
            count_business_days(datetime.date(2024, 1, 8),
                                 datetime.date(2024, 1, 15)),
            cal.count_business_days(datetime.date(2024, 1, 8),
                                     datetime.date(2024, 1, 15)),
        )

    def test_module_add_matches_class(self):
        cal = BusinessDayCalendar()
        self.assertEqual(
            add_business_days(datetime.date(2024, 1, 8), 3),
            cal.add_business_days(datetime.date(2024, 1, 8), 3),
        )


class TestHolidaysProperty(unittest.TestCase):
    def test_returns_defensive_copy(self):
        h = {datetime.date(2024, 1, 1)}
        cal = BusinessDayCalendar(h)
        out = cal.holidays
        out.add(datetime.date(2024, 7, 4))
        # Internal state must not change
        self.assertEqual(cal.holidays, h)


if __name__ == "__main__":
    unittest.main()
