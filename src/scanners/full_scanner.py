from typing import List
from collections import defaultdict
import discord


# Custom libs

from .scanner import Scanner
from . import FrequencyScanner, CompositionScanner, OtherScanner, EmotesScanner
from data_types import Frequency, Composition, Other, Emote, get_emote_dict
from logs import ChannelLogs, MessageLog


class FullScanner(Scanner):
    @staticmethod
    def help() -> str:
        return "```\n"
        +"%full : Show full statistics\n"
        +"arguments:\n"
        +"* @member : filter for one or more member\n"
        +"* #channel : filter for one or more channel\n"
        +"Example: %full #mychannel1 @user\n"
        +"```"

    def __init__(self):
        super().__init__(
            help=FullScanner.help(),
            intro_context="Full analysis",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        guild = message.channel.guild
        self.freq = Frequency()
        self.comp = Composition()
        self.other = Other()
        # Create emotes dict from custom emojis of the guild
        # Create emotes dict from custom emojis of the guild
        self.emotes = get_emote_dict(message.channel.guild)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        FrequencyScanner.analyse_message(message, self.freq, self.raw_members)
        CompositionScanner.analyse_message(message, self.comp, self.raw_members)
        OtherScanner.analyse_message(channel, message, self.other, self.raw_members)
        EmotesScanner.analyse_message(
            message, self.emotes, self.raw_members, all_emojis=True
        )
        return not message.bot and (
            len(self.raw_members) == 0 or message.author in self.raw_members
        )

    def get_results(self, intro: str) -> List[str]:
        FrequencyScanner.compute_results(self.freq)
        CompositionScanner.compute_results(self.comp, self.emotes)
        OtherScanner.compute_results(self.other, self.emotes)
        res = [intro]
        res += ["__Frequency__:"]
        res += self.freq.to_string()
        res += ["__Composition__:"]
        res += self.comp.to_string()
        res += ["__Other__:"]
        res += self.other.to_string(
            show_top_channel=len(self.channels) > 1,
            show_mentioned=(len(self.members) != 1),
        )
        return res
