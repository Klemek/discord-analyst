from typing import List
from datetime import timedelta

from utils import str_date, str_datetime, from_now


class Frequency:
    def __init__(self):
        self.earliest = None
        self.latest = None
        self.longest_break = timedelta(seconds=0)
        self.longest_break_start = None

    def to_string(self) -> List[str]:
        return [
            f"**earliest message:** {str_date(self.earliest)} ({from_now(self.earliest)})",
            f"**latest message:** {str_date(self.latest)} ({from_now(self.latest)})",
            # "**msg/day:** n",
            # "**busiest day of week:** dd (avg. n msg)",
            # "**busiest day ever:** jj/mm/yyyy (n days ago) (n msg)",
            # "**msg/hour:** n",
            # "**busiest hour of day:** hh (avg. n msg)",
            # "**busiest hour ever:** hh jj/mm/yyyy (n days ago) (n msg)",
            f"**longest break:** {int(self.longest_break.total_seconds() / 3600):,} hours from {str_datetime(self.longest_break_start)} ({from_now(self.earliest)})",
        ]
