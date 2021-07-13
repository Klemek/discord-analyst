from typing import List
from datetime import timedelta
import calendar

from utils import (
    str_date,
    str_datetime,
    from_now,
    plural,
    percent,
    precise,
    top_key,
    mention,
)


class Frequency:
    def __init__(self):
        self.dates = []
        self.longest_break = timedelta(seconds=0)
        self.longest_break_start = None
        self.hours = {i: {j: 0 for j in range(24)} for i in range(7)}
        self.busiest_day = None
        self.busiest_day_count = 0
        self.busiest_hour = None
        self.busiest_hour_count = 0
        self.streaks = []
        self.last_author = None
        self.last_streak_start = None
        self.last_streak_author = None
        self.longest_streak = None
        self.longest_streak_start = None
        self.longest_streak_author = None

    def to_string(
        self,
        *,
        member_specific: bool,
    ) -> List[str]:
        self.dates.sort()
        delta = self.dates[-1] - self.dates[0]
        if delta.days == 0:
            delta = timedelta(days=1)
        total_msg = len(self.dates)

        week = {i: sum(self.hours[i].values()) for i in range(7)}
        day = {j: sum(self.hours[i][j] for i in range(7)) for j in range(24)}

        busiest_weekday = top_key(week)
        busiest_hour = top_key(day)
        quietest_weekday = top_key(week, reverse=True)
        quietest_hour = top_key(day, reverse=True)
        n_weekdays = delta.days // 7
        if (
            self.dates[0].weekday() <= busiest_weekday
            and self.dates[-1].weekday() >= busiest_weekday
        ) or n_weekdays == 0:
            n_weekdays += 1
        n_hours = delta.days
        if self.dates[0].hour <= busiest_hour and self.dates[-1].hour >= busiest_hour:
            n_hours += 1
        ret = [
            f"- **earliest message**: {str_datetime(self.dates[0])} ({from_now(self.dates[0])})",
            f"- **latest message**: {str_datetime(self.dates[-1])} ({from_now(self.dates[-1])})",
            f"- **messages/day**: {precise(total_msg/delta.days, precision=3)}",
            f"- **busiest day of week**: {calendar.day_name[busiest_weekday]} (~{precise(week[busiest_weekday]/n_weekdays, precision=3)} msg, {percent(week[busiest_weekday]/total_msg)})",
            f"- **quietest day of week**: {calendar.day_name[quietest_weekday]} (~{precise(week[quietest_weekday]/n_weekdays, precision=3)} msg, {percent(week[quietest_weekday]/total_msg)})"
            if week[quietest_weekday] > 0 else "",
            f"- **busiest day ever**: {str_date(self.busiest_day)} ({from_now(self.busiest_day)}, {self.busiest_day_count} msg)"
            if self.busiest_day is not None
            else "",
            f"- **messages/hour**: {precise(total_msg*3600/delta.total_seconds(), precision=3)}",
            f"- **busiest hour of day**: {busiest_hour:0>2}:00 (~{precise(day[busiest_hour]/n_hours, precision=3)} msg, {percent(day[busiest_hour]/total_msg)})",
            f"- **quietest hour of day**: {quietest_hour:0>2}:00 (~{precise(day[quietest_hour]/n_hours, precision=3)} msg, {percent(day[quietest_hour]/total_msg)})"
            if day[quietest_hour] > 0 else "",
            f"- **busiest hour ever**: {str_datetime(self.busiest_hour)} ({from_now(self.busiest_hour)}, {self.busiest_hour_count} msg)",
            f"- **longest break**: {plural(round(self.longest_break.total_seconds()/3600), 'hour')} ({plural(self.longest_break.days,'day')}) from {str_datetime(self.longest_break_start)} ({from_now(self.longest_break_start)})",
            f"- **avg. streak**: {precise(sum(self.streaks)/len(self.streaks), precision=3)} msg",
            f"- **longest streak**: {self.longest_streak:,} msg from {str_datetime(self.longest_streak_start)} ({from_now(self.longest_streak_start)})"
            if member_specific
            else f"- **longest streak**: {mention(self.longest_streak_author)} ({self.longest_streak:,} msg from {str_datetime(self.longest_streak_start)}, {from_now(self.longest_streak_start)})",
        ]
        return ret
