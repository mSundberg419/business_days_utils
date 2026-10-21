# business_days_utils

Count working days between dates with a holiday calendar.

```python
import datetime
from business_days_utils import BusinessDayCalendar, count_business_days, add_business_days

holidays = {datetime.date(2024, 1, 1)}
cal = BusinessDayCalendar(holidays)

cal.count_business_days(datetime.date(2024, 1, 1), datetime.date(2024, 1, 8))  # 4
cal.add_business_days(datetime.date(2024, 1, 4), 3)                            # 2024-01-09

# Without holidays:
count_business_days(datetime.date(2024, 1, 1), datetime.date(2024, 1, 8))  # 5
add_business_days(datetime.date(2024, 1, 4), 3)                              # 2024-01-09
```

## Why this exists

Every project that deals with contract deadlines, settlement dates, or SLAs
reimplements the same loop: walk forward through days, skip Saturday and
Sunday, skip a hand-maintained list of holidays. The trade-off here is
deliberate simplicity over configurability. The weekend is fixed as
Saturday/Sunday and there is no locale model; if your calendar uses a
Friday/Saturday weekend, this library is the wrong tool.

## Edge cases worth knowing

- `count_business_days(start, end)` uses a **half-open interval**: `end` is not
counted. This lets you express "all of March" as
`count_business_days(march_1, april_1)` without an off-by-one.

- `add_business_days(start, 0)` does **not** return `start` unchanged if
`start` falls on a weekend or holiday. It rolls forward to the next business
day. This is the choice that makes the function useful for normalising a
date to a valid settlement date. If you need strict zero-means-noop, check
`is_business_day` yourself before calling.

- Holidays that fall on a weekend are silently redundant — they are already
non-business days and listing them again changes nothing.

- `count_business_days` with `start > end` returns the negative of the
reversed count, so signed durations work without branching.
