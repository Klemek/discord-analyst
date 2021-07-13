from typing import List
from datetime import datetime
import discord


# Custom libs

from .scanner import Scanner
from data_types import Frequency
from logs import ChannelLogs, MessageLog
from utils import generate_help


class FrequencyScanner(Scanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "freq",
            "(BETA) Show frequency-related statistics",
            args=[
                "graph - plot hours of week",
            ],
        )

    def __init__(self):
        super().__init__(
            valid_args=["all", "everyone", "graph"],
            help=FrequencyScanner.help(),
            intro_context="Frequency",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.freq = Frequency()
        self.all_messages = "all" in args or "everyone" in args
        self.member_specific = len(self.members) > 0
        self.to_graph = "graph" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return FrequencyScanner.analyse_message(
            message, self.freq, self.raw_members, all_messages=self.all_messages
        )

    def get_results(self, intro: str) -> List[str]:
        FrequencyScanner.compute_results(self.freq)
        if self.to_graph:
            res = self.freq.to_graph()
        else:
            res = [intro]
            res += self.freq.to_string(
                member_specific=self.member_specific,
            )
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog,
        freq: Frequency,
        raw_members: List[int],
        *,
        all_messages: bool,
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if (
            (not message.bot or all_messages)
            and len(raw_members) == 0
            or message.author in raw_members
        ):
            impacted = True
            freq.dates += [message.created_at]
            if message.author == freq.last_author:
                freq.streaks[-1] += 1
            else:
                if len(freq.streaks) > 0 and (
                    freq.longest_streak is None
                    or freq.streaks[-1] > freq.longest_streak
                ):
                    freq.longest_streak = freq.streaks[-1]
                    freq.longest_streak_start = freq.last_streak_start
                    freq.longest_streak_author = freq.last_streak_author
                freq.streaks += [1]
                freq.last_streak_start = message.created_at
                freq.last_streak_author = message.author
        freq.last_author = message.author
        return impacted

    @staticmethod
    def compute_results(freq: Frequency):
        freq.dates.sort()
        latest = freq.dates[0]
        current_day = 0
        current_day_date = freq.dates[0]
        current_day_count = 0
        current_hour_buffer = []
        for date in freq.dates:
            # calculate longest break
            delay = date - latest
            if delay > freq.longest_break:
                freq.longest_break = delay
                freq.longest_break_start = latest
            latest = date
            # calculate busiest weekday / hours
            freq.hours[date.weekday()][date.hour] += 1
            # calculate busiest day ever
            start_delta = date - freq.dates[0]
            if start_delta.days > current_day:
                if current_day_count > freq.busiest_day_count:
                    freq.busiest_day_count = current_day_count
                    freq.busiest_day = current_day_date
                current_day = start_delta.days
                current_day_date = date
                current_day_count = 0
            else:
                current_day_count += 1
            # calculate busiest hour ever
            while (
                len(current_hour_buffer) > 0
                and (date - current_hour_buffer[0]).total_seconds() > 3600
            ):
                current_hour_buffer.pop(0)
            current_hour_buffer += [date]
            if len(current_hour_buffer) > freq.busiest_hour_count:
                freq.busiest_hour = current_hour_buffer[0]
                freq.busiest_hour_count = len(current_hour_buffer)
