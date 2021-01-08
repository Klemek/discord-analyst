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
        +"* @member : filter for one or more member\n"
        +"* #channel : filter for one or more channel\n"
        +"Example: %freq #mychannel1 @user\n"
        +"```"

    def __init__(self):
        super().__init__(
            help=FrequencyScanner.help(),
            intro_context="frequency",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.freq = Frequency()
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return FrequencyScanner.analyse_message(message, self.freq, self.raw_members)

    def get_results(self, intro: str) -> List[str]:
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
            date = message.created_at
            # order is latest to earliest
            if freq.latest is None:
                freq.earliest = date
                freq.latest = date

            delay = freq.earliest - date
            if delay > freq.longest_break:
                freq.longest_break = delay
                freq.longest_break_start = date

            # TODO

            freq.earliest = date
        return impacted
