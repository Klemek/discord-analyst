from typing import List
import discord


# Custom libs

from .scanner import Scanner
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

    async def compute_args(self, message: discord.Message, *args: str) -> bool:
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return FrequencyScanner.analyse_message(message, self.raw_members)

    def get_results(self, intro: str) -> List[str]:
        res = [intro]
        # TODO
        return res

    @staticmethod
    def analyse_message(message: MessageLog, raw_members: List[int]) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if not message.bot and (len(raw_members) == 0 or message.author in raw_members):
            impacted = True
            # TODO
        return impacted
