from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import (
    COMMON_HELP_ARGS,
    plural,
    precise,
    mention,
    alt_mention,
    role_mention,
    channel_mention,
)


class MentionsScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%mentions: Rank mentions by their usage\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* <n> - top <n> mentions, default is 10\n"
            + "* all - show role/channel/everyone/here mentions\n"
            + "Example: %mentions 10 #mychannel1 #mychannel2 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all"],
            help=MentionsScanner.help(),
            intro_context="Mention usage",
        )
        self.top = 10

    async def init(self, message: discord.Message, *args: str) -> bool:
        # get max emotes to view
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        # check other args
        self.all_mentions = "all" in args
        # Create mentions dict
        self.mentions = defaultdict(Counter)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return MentionsScanner.analyse_message(
            message, self.mentions, self.raw_members, all_mentions=self.all_mentions
        )

    def get_results(self, intro: str) -> List[str]:
        names = [name for name in self.mentions]
        names.sort(key=lambda name: self.mentions[name].score(), reverse=True)
        names = names[: self.top]
        # Get the total of all emotes used
        usage_count = sum([mention.usages for mention in self.mentions.values()])
        res = [intro]
        res += [
            self.mentions[name].to_string(
                names.index(name),
                name,
                total_usage=usage_count,
            )
            for name in names
        ]
        res += [
            f"Total: {plural(usage_count,'time')} ({precise(usage_count/self.msg_count)}/msg)"
        ]
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog,
        mentions: Dict[str, Counter],
        raw_members: List[int],
        *,
        all_mentions: bool,
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if not message.bot and len(raw_members) == 0 or message.author in raw_members:
            impacted = True
            for member_id in message.mentions:
                name = mention(member_id)
                count = message.content.count(name) + message.content.count(
                    alt_mention(member_id)
                )
                mentions[name].update_use(count, message.created_at)
            if all_mentions:
                for role_id in message.role_mentions:
                    name = role_mention(role_id)
                    mentions[name].update_use(
                        message.content.count(name), message.created_at
                    )
                for channel_id in message.channel_mentions:
                    name = channel_mention(channel_id)
                    mentions[name].update_use(
                        message.content.count(name), message.created_at
                    )
                if "@everyone" in message.content:
                    mentions["@\u200beveryone"].update_use(
                        message.content.count("@everyone"), message.created_at
                    )
                if "@here" in message.content:
                    mentions["@\u200bhere"].update_use(
                        message.content.count("@here"), message.created_at
                    )
        return impacted
