from typing import List
from datetime import timedelta
import calendar

from utils import str_date, str_datetime, from_now, plural, percent, precise, top_key


class Frequency:
    def __init__(self):
        self.dates = []
        self.longest_break = timedelta(seconds=0)
        self.longest_break_start = None
        self.week = {i: 0 for i in range(7)}
        self.day = {i: 0 for i in range(24)}
        self.busiest_day = None
        self.busiest_day_count = 0
        self.busiest_hour = None
        self.busiest_hour_count = 0

    def to_string(self) -> List[str]:
        delta = self.dates[-1] - self.dates[0]
        total_msg = len(self.dates)
        busiest_weekday = top_key(self.week)
        busiest_hour = top_key(self.day)
        n_weekdays = delta.days // 7
        if (
            self.dates[0].weekday() <= busiest_weekday
            and self.dates[-1].weekday() >= busiest_weekday
        ):
            n_weekdays += 1
        n_hours = delta.days
        if self.dates[0].hour <= busiest_hour and self.dates[-1].hour >= busiest_hour:
            n_hours += 1
        return [
            f"- **earliest message**: {str_datetime(self.dates[0])} ({from_now(self.dates[0])})",
            f"- **latest message**: {str_datetime(self.dates[-1])} ({from_now(self.dates[-1])})",
            f"- **messages/day**: {precise(total_msg/delta.days, precision=3)}",
            f"- **busiest day of week**: {calendar.day_name[busiest_weekday]} (~{precise(self.week[busiest_weekday]/n_weekdays, precision=3)} msg, {percent(self.week[busiest_weekday]/total_msg)})",
            f"- **busiest day ever**: {str_date(self.busiest_day)} ({from_now(self.busiest_day)}) ({self.busiest_day_count} msg)",
            f"- **messages/hour**: {precise(total_msg*3600/delta.total_seconds(), precision=3)}",
            f"- **busiest hour of day**: {busiest_hour:0>2}:00 (~{precise(self.day[busiest_hour]/n_hours, precision=3)} msg, {percent(self.day[busiest_hour]/total_msg)})",
            f"- **busiest hour ever**: {str_datetime(self.busiest_hour)} ({from_now(self.busiest_hour)}) ({self.busiest_hour_count} msg)",
            f"- **longest break**: {plural(round(self.longest_break.total_seconds()/3600), 'hour')} ({plural(self.longest_break.days,'day')}) from {str_datetime(self.longest_break_start)} ({from_now(self.longest_break_start)})",
        ]
