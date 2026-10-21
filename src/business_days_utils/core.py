"""Count working days between dates with a holiday calendar.

The module exposes a BusinessDayCalendar class that wraps a set of holiday
dates and provides counting / shifting operations that skip weekends and
holidays.  The Monday-to-Friday convention is hard-coded because it is
what "business day" means in the contexts this library was written for
(banking settlement, contract deadlines).  Saturday and Sunday are always
non-business days regardless of locale; if you need Friday-Saturday
weekends, this is the wrong library.

All dates are datetime.date objects — timezone-aware datetimes are
intentionally out of scope because holiday calendars are almost always
date-only and mixing dates and datetimes leads to silent bugs.
"""

from __future__ import annotations

import datetime
from typing import Iterable, Set


_WEEKDAYS = {0, 1, 2, 3, 4}  # Mon..Fri; date.weekday() returns 0 for Monday


def _normalise_holidays(holidays: Iterable[datetime.date]) -> Set[datetime.date]:
    """Coerce an arbitrary iterable of dates into a set.

    A set gives O(1) membership checks which matters when shifting many
    days; the original container is left untouched so the caller can pass
    a list, tuple, or generator without surprise.
    """
    return {datetime.date(d.year, d.month, d.day) for d in holidays}


class BusinessDayCalendar:
    """Stateless wrapper around a fixed set of holiday dates.

    Instantiate once with your holiday calendar and call the methods for
    the life of the program.  The object holds no mutable state, so it is
    safe to share across threads.
    """

    __slots__ = ("_holidays",)

    def __init__(self, holidays: Iterable[datetime.date] = ()) -> None:
        self._holidays: Set[datetime.date] = _normalise_holidays(holidays)

    @property
    def holidays(self) -> Set[datetime.date]:
        """Return a defensive copy so callers cannot mutate our state."""
        return set(self._holidays)

    def is_business_day(self, date: datetime.date) -> bool:
        """True iff *date* is a weekday and not in the holiday set."""
        return date.weekday() in _WEEKDAYS and date not in self._holidays

    def _next_business_day(self, date: datetime.date) -> datetime.date:
        """Smallest business day strictly greater than *date*.

        Used by add_business_days; exposed only as a helper so the public
        API stays small.
        """
        d = date + datetime.timedelta(days=1)
        while not self.is_business_day(d):
            d += datetime.timedelta(days=1)
        return d

    def _previous_business_day(self, date: datetime.date) -> datetime.date:
        """Largest business day strictly less than *date*."""
        d = date - datetime.timedelta(days=1)
        while not self.is_business_day(d):
            d -= datetime.timedelta(days=1)
        return d

    # ------------------------------------------------------------------
    # Counting
    # ------------------------------------------------------------------
    def count_business_days(
        self, start: datetime.date, end: datetime.date
    ) -> int:
        """Number of business days in the half-open interval [start, end).

        The interval is half-open on the end side: the day *end* itself is
        NOT counted.  This matches the convention used by most spreadsheet
        NETWORKDLS-style functions and makes counting a range like
        'all of March' a simple `count(month_start, next_month_start)`.

        If start > end the result is the negation of count(end, start),
        so callers can compute signed durations without branching.
        """
        if start == end:
            return 0
        if start > end:
            return -self.count_business_days(end, start)

        # Walk forward day by day.  A calendar-aware jump would be faster
        # for huge ranges, but the simple loop is obviously correct and
        # avoids premature complexity; ranges here are typically a few
        # years at most.
        count = 0
        current = start
        while current < end:
            if self.is_business_day(current):
                count += 1
            current += datetime.timedelta(days=1)
        return count

    # ------------------------------------------------------------------
    # Shifting
    # ------------------------------------------------------------------
    def add_business_days(
        self, start: datetime.date, n: int
    ) -> datetime.date:
        """Return the date *n* business days after *start*.

        A count of zero is the single most-requested edge case: callers
        usually want 'the next business day on or after start' semantics.
        We interpret n == 0 as 'leave start untouched if it is already a
        business day, otherwise roll forward to the next business day'.
        This is a deliberate choice — the alternative ('return start
        unchanged') makes the function useless for normalisation, which is
        the only reason to pass zero.

        Positive n shifts forward, negative n shifts backward.
        """
        if n == 0:
            return start if self.is_business_day(start) else self._next_business_day(start)

        if n > 0:
            current = start
            remaining = n
            # If start is not a business day, the first step lands on the
            # next business day without consuming a unit — this matches the
            # 'advance to the next business day' intuition.
            if not self.is_business_day(current):
                current = self._next_business_day(current)
            while remaining > 0:
                current = self._next_business_day(current)
                remaining -= 1
            return current

        # n < 0
        current = start
        remaining = -n
        if not self.is_business_day(current):
            current = self._previous_business_day(current)
        while remaining > 0:
            current = self._previous_business_day(current)
            remaining -= 1
        return current


# ----------------------------------------------------------------------
# Module-level convenience functions
# ----------------------------------------------------------------------
_default_calendar = BusinessDayCalendar()


def count_business_days(start: datetime.date, end: datetime.date) -> int:
    """Shortcut for BusinessDayCalendar().count_business_days(start, end).

    Uses a shared empty-holiday instance so repeated calls do not rebuild
    a calendar.  Pass a real BusinessDayCalendar if you have holidays.
    """
    return _default_calendar.count_business_days(start, end)


def add_business_days(start: datetime.date, n: int) -> datetime.date:
    """Shortcut for BusinessDayCalendar().add_business_days(start, n)."""
    return _default_calendar.add_business_days(start, n)
