from typing import List
from collections import defaultdict
import discord


# Custom libs

from .scanner import Scanner
from . import FrequencyScanner, CompositionScanner, PresenceScanner, EmotesScanner
from data_types import Frequency, Composition, Presence, get_emote_dict
from logs import ChannelLogs, MessageLog
from utils import COMMON_HELP_ARGS


class FullScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%scan : Show full statistics\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "Example: %scan #mychannel1 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            help=FullScanner.help(),
            intro_context="Full analysis",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        guild = message.channel.guild
        self.freq = Frequency()
        self.comp = Composition()
        self.pres = Presence()
        self.member_specific = len(self.members) > 0
        # Create emotes dict from custom emojis of the guild
        self.emotes = get_emote_dict(message.channel.guild)
        if self.member_specific:
            self.emotes_all = get_emote_dict(message.channel.guild)
        else:
            self.emotes_all = {}
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        FrequencyScanner.analyse_message(message, self.freq, self.raw_members)
        CompositionScanner.analyse_message(message, self.comp, self.raw_members)
        PresenceScanner.analyse_message(channel, message, self.pres, self.raw_members)
        EmotesScanner.analyse_message(
            message, self.emotes, self.raw_members, all_emojis=True
        )
        if self.member_specific:
            EmotesScanner.analyse_message(message, self.emotes_all, [], all_emojis=True)
        return not message.bot and (
            len(self.raw_members) == 0 or message.author in self.raw_members
        )

    def get_results(self, intro: str) -> List[str]:
        FrequencyScanner.compute_results(self.freq)
        CompositionScanner.compute_results(self.comp, self.emotes)
        PresenceScanner.compute_results(self.pres, self.emotes, self.emotes_all)
        res = [intro]
        res += ["__Frequency__:"]
        res += self.freq.to_string()
        res += ["__Composition__:"]
        res += self.comp.to_string()
        res += ["__Presence__:"]
        res += self.pres.to_string(
            show_top_channel=len(self.channels) > 1,
            member_specific=self.member_specific,
        )
        return res
