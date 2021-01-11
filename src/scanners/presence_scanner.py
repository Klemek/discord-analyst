from typing import List
import discord


# Custom libs

from .scanner import Scanner
from data_types import Presence
from logs import ChannelLogs, MessageLog
from utils import COMMON_HELP_ARGS


class PresenceScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%pres : Show presence statistics\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "Example: %pres #mychannel1 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            help=PresenceScanner.help(),
            intro_context="Presence",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.pres = Presence()
        self.total_msg = 0
        self.member_specific = len(self.members) > 0
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        self.total_msg += 1
        return PresenceScanner.analyse_message(
            channel, message, self.pres, self.raw_members
        )

    def get_results(self, intro: str) -> List[str]:
        res = [intro]
        res += self.pres.to_string(
            self.msg_count,
            self.total_msg,
            show_top_channel=(len(self.channels) > 1),
            member_specific=self.member_specific,
        )
        return res

    @staticmethod
    def analyse_message(
        channel: ChannelLogs,
        message: MessageLog,
        pres: Presence,
        raw_members: List[int],
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if not message.bot and (len(raw_members) == 0 or message.author in raw_members):
            impacted = True
            pres.channel_usage[channel.id] += 1
            for mention in message.mentions:
                pres.mention_others[mention] += 1
        pres.channel_total[channel.id] += 1
        if len(raw_members) > 0:
            for mention in message.mentions:
                if mention in raw_members:
                    pres.mentions[message.author] += 1
                pres.mention_count += 1
            for reaction in message.reactions:
                pres.used_reaction_total += len(message.reactions[reaction])
                for member_id in message.reactions[reaction]:
                    if member_id in raw_members:
                        pres.reactions[reaction] += 1
        else:
            pres.mention_count += len(message.mentions)
            for reaction in message.reactions:
                pres.used_reaction_total += len(message.reactions[reaction])
                pres.reactions[reaction] += len(message.reactions[reaction])
        return impacted
