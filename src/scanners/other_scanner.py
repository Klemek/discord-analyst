from typing import List, Dict
import discord


# Custom libs

from .scanner import Scanner
from . import EmotesScanner
from data_types import Other, Emote, get_emote_dict
from logs import ChannelLogs, MessageLog


class OtherScanner(Scanner):
    @staticmethod
    def help() -> str:
        return "```\n"
        +"%other : Show other statistics\n"
        +"arguments:\n"
        +"* @member : filter for one or more member\n"
        +"* #channel : filter for one or more channel\n"
        +"Example: %other #mychannel1 @user\n"
        +"```"

    def __init__(self):
        super().__init__(
            help=OtherScanner.help(),
            intro_context="Other data",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.other = Other()
        # Create emotes dict from custom emojis of the guild
        self.emotes = get_emote_dict(message.channel.guild)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        ret = OtherScanner.analyse_message(message, self.other, self.raw_members)
        ret &= EmotesScanner.analyse_message(
            message, self.emotes, self.raw_members, all_emojis=True
        )
        return ret

    def get_results(self, intro: str) -> List[str]:
        OtherScanner.compute_results(self.other, self.emotes)
        res = [intro]
        res += self.other.to_string()
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog, other: Other, raw_members: List[int]
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if len(raw_members) == 0 or message.author in raw_members:
            impacted = True
            pass  # TODO
        return impacted

    @staticmethod
    def compute_results(other: Other, emotes: Dict[str, Emote]):
        pass  # TODO
