from typing import List, Dict
import discord


# Custom libs

from .scanner import Scanner
from . import EmotesScanner
from data_types import Presence, Emote, get_emote_dict
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
        # Create emotes dict from custom emojis of the guild
        self.emotes = get_emote_dict(message.channel.guild)
        if self.member_specific:
            self.emotes_all = get_emote_dict(message.channel.guild)
        else:
            self.emotes_all = {}
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        self.total_msg += 1
        EmotesScanner.analyse_message(
            message, self.emotes, self.raw_members, all_emojis=True
        )
        if self.member_specific:
            EmotesScanner.analyse_message(message, self.emotes_all, [], all_emojis=True)
        return PresenceScanner.analyse_message(
            channel, message, self.pres, self.raw_members
        )

    def get_results(self, intro: str) -> List[str]:
        PresenceScanner.compute_results(self.pres, self.emotes, self.emotes_all)
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
            pres.msg_count += 1
            for mention in message.mentions:
                pres.mention_others[mention] += 1
        pres.channel_total[channel.id] += 1
        for mention in message.mentions:
            if mention in raw_members:
                pres.mentions[message.author] += 1
            pres.mention_count += 1
        return impacted

    @staticmethod
    def compute_results(
        pres: Presence, emotes: Dict[str, Emote], emotes_all: Dict[str, Emote]
    ):
        # calculate total reactions
        pres.used_reaction_total = sum([emote.reactions for emote in emotes.values()])
        if len(emotes_all) > 0:
            pres.used_reaction_all_total = sum(
                [emote.reactions for emote in emotes_all.values()]
            )
        if pres.used_reaction_total > 0:
            # calculate most used reaction
            pres.most_used_reaction = sorted(emotes, key=lambda k: emotes[k].reactions)[
                -1
            ]
            pres.most_used_reaction_count = emotes[pres.most_used_reaction].reactions
