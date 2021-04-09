from typing import List
import discord


# Custom libs

from .scanner import Scanner
from . import FrequencyScanner, CompositionScanner, PresenceScanner
from data_types import Frequency, Composition, Presence
from logs import ChannelLogs, MessageLog
from utils import generate_help


class FullScanner(Scanner):
    @staticmethod
    def help() -> str:
        return generate_help("scan", "Show full statistics")

    def __init__(self):
        super().__init__(
            valid_args=["all", "everyone"],
            help=FullScanner.help(),
            intro_context="Full analysis",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.freq = Frequency()
        self.compo = Composition()
        self.pres = Presence()
        self.member_specific = len(self.members) > 0
        self.all_messages = "all" in args or "everyone" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        FrequencyScanner.analyse_message(
            message, self.freq, self.raw_members, all_messages=self.all_messages
        )
        CompositionScanner.analyse_message(
            message, self.compo, self.raw_members, all_messages=self.all_messages
        )
        PresenceScanner.analyse_message(
            channel,
            message,
            self.pres,
            self.raw_members,
            all_messages=self.all_messages,
        )
        return (
            (not message.bot or self.all_messages)
            and len(self.raw_members) == 0
            or message.author in self.raw_members
        )

    def get_results(self, intro: str) -> List[str]:
        FrequencyScanner.compute_results(self.freq)
        res = [intro]
        res += ["__Frequency__:"]
        res += self.freq.to_string(member_specific=self.member_specific)
        res += ["__Composition__:"]
        res += self.compo.to_string(self.msg_count)
        res += ["__Presence__:"]
        res += self.pres.to_string(
            self.msg_count,
            self.total_msg,
            show_top_channel=len(self.channels) > 1,
            member_specific=self.member_specific,
            chan_count=len(self.channels) if not self.full else None,
        )
        return res
