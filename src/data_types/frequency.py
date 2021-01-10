from typing import List
from datetime import timedelta

from utils import str_date, str_datetime, from_now


class Frequency:
    def __init__(self):
        self.dates = []
        self.longest_break = timedelta(seconds=0)
        self.longest_break_start = None

    def to_string(self) -> List[str]:
        return [
            f"**earliest message:** {str_datetime(self.dates[0])} ({from_now(self.dates[0])})",
            f"**latest message:** {str_datetime(self.dates[-1])} ({from_now(self.dates[-1])})",
            # "**msg/day:** n",
            # "**busiest day of week:** dd (avg. n msg)",
            # "**busiest day ever:** jj/mm/yyyy (n days ago) (n msg)",
            # "**msg/hour:** n",
            # "**busiest hour of day:** hh (avg. n msg)",
            # "**busiest hour ever:** hh jj/mm/yyyy (n days ago) (n msg)",
            f"**longest break:** {int(self.longest_break.total_seconds() / 3600):,} hours ({int(self.longest_break.days):,} days) from {str_datetime(self.longest_break_start)} ({from_now(self.longest_break_start)})",
        ]
