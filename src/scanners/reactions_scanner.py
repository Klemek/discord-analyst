from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import COMMON_HELP_ARGS, mention, channel_mention


class ReactionsScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%react: Rank users by their reactions\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* <n> - top <n>, default is 10\n"
            + "Example: %react 10 #channel\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            help=ReactionsScanner.help(),
            intro_context="Reactions",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        # get max emotes to view
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        # Create mentions dict
        self.messages = defaultdict(Counter)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return ReactionsScanner.analyse_message(
            channel.id,
            message,
            self.messages,
            self.raw_members,
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
                mention(name),
                total_usage=usage_count,
                counted="reaction",
                transform=lambda id: f" in {channel_mention(id)}",
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
    ) -> bool:
        impacted = True
        for reaction in message.reactions:
            for member_id in message.reactions[reaction]:
                if len(raw_members) == 0 or member_id in raw_members:
                    messages[member_id].update_use(1, message.created_at, channel_id)
        return impacted
