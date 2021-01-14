from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import COMMON_HELP_ARGS, plural, precise, mention, alt_mention


class MessagesScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%msg: Rank users mentions by their messages\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* <n> - top <n>, default is 10\n"
            + "* all - include bots\n"
            + "Example: %msg 10 #channel\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all"],
            help=MessagesScanner.help(),
            intro_context="Messages",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        # get max emotes to view
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        self.all_mentions = "all" in args
        # Create mentions dict
        self.messages = defaultdict(Counter)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return MessagesScanner.analyse_message(
            message, self.messages, self.raw_members, all_mentions=self.all_mentions
        )

    def get_results(self, intro: str) -> List[str]:
        names = [name for name in self.messages]
        names.sort(key=lambda name: self.messages[name].score(), reverse=True)
        names = names[: self.top]
        usage_count = sum([message.usages for message in self.messages.values()])
        res = [intro]
        res += [
            self.messages[name].to_string(
                names.index(name),
                mention(name),
                total_usage=usage_count,
                counted="message",
            )
            for name in names
        ]
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog,
        messages: Dict[str, Counter],
        raw_members: List[int],
        *,
        all_mentions: bool,
    ) -> bool:
        impacted = False
        if not message.bot or all_mentions:
            impacted = True
            messages[message.author].update_use(1, message.created_at)
        return impacted
