from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import COMMON_HELP_ARGS, mention, channel_mention


class ChannelsScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%chan: Rank channels by their messages\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* <n> - top <n>, default is 10\n"
            + "* all - include bots\n"
            + "Example: %chan 10 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all"],
            help=ChannelsScanner.help(),
            intro_context="Channels",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        # get max emotes to view
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        self.all_messages = "all" in args
        # Create mentions dict
        self.messages = defaultdict(Counter)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return ChannelsScanner.analyse_message(
            channel.id,
            message,
            self.messages,
            self.raw_members,
            all_messages=self.all_messages,
        )

    def get_results(self, intro: str) -> List[str]:
        names = [name for name in self.messages]
        names.sort(key=lambda name: self.messages[name].score(), reverse=True)
        names = names[: self.top]
        usage_count = Counter.total(self.messages)
        res = [intro]
        res += [
            self.messages[name].to_string(
                names.index(name),
                channel_mention(name),
                total_usage=usage_count,
                counted="message",
                transform=lambda id: f" by {mention(id)}",
            )
            for name in names
        ]
        return res

    @staticmethod
    def analyse_message(
        channel_id: int,
        message: MessageLog,
        messages: Dict[str, Counter],
        raw_members: List[int],
        *,
        all_messages: bool,
    ) -> bool:
        impacted = False
        if not message.bot or all_messages:
            impacted = True
            messages[channel_id].update_use(1, message.created_at, message.author)
        return impacted
