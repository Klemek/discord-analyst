from typing import List
from datetime import datetime
import discord


# Custom libs

from .scanner import Scanner
from data_types import Frequency
from logs import ChannelLogs, MessageLog


class FrequencyScanner(Scanner):
    @staticmethod
    def help() -> str:
        return "```\n"
        +"%freq : Show frequency-related statistics\n"
        +"arguments:\n"
        +"* @member/me : filter for one or more member\n"
        +"* #channel/here : filter for one or more channel\n"
        +"Example: %freq #mychannel1 @user\n"
        +"```"

    def __init__(self):
        super().__init__(
            help=FrequencyScanner.help(),
            intro_context="Frequency",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.freq = Frequency()
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return FrequencyScanner.analyse_message(message, self.freq, self.raw_members)

    def get_results(self, intro: str) -> List[str]:
        FrequencyScanner.compute_results(self.freq)
        res = [intro]
        res += self.freq.to_string()
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog, freq: Frequency, raw_members: List[int]
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if len(raw_members) == 0 or message.author in raw_members:
            impacted = True
            freq.dates += [message.created_at]
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
            freq.week[date.weekday()] += 1
            freq.day[date.hour] += 1
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
