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
        self.compo = Composition()
        self.pres = Presence()
        self.member_specific = len(self.members) > 0
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        FrequencyScanner.analyse_message(message, self.freq, self.raw_members)
        CompositionScanner.analyse_message(message, self.compo, self.raw_members)
        PresenceScanner.analyse_message(channel, message, self.pres, self.raw_members)
        return not message.bot and (
            len(self.raw_members) == 0 or message.author in self.raw_members
        )

    def get_results(self, intro: str) -> List[str]:
        FrequencyScanner.compute_results(self.freq)
        res = [intro]
        res += ["__Frequency__:"]
        res += self.freq.to_string()
        res += ["__Composition__:"]
        res += self.compo.to_string(self.msg_count)
        res += ["__Presence__:"]
        res += self.pres.to_string(
            self.msg_count,
            self.total_msg,
            show_top_channel=len(self.channels) > 1,
            member_specific=self.member_specific,
        )
        return res
