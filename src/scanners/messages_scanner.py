from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import generate_help, mention, channel_mention


class MessagesScanner(Scanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "msg",
            "Rank users by their messages",
            args=["<n> - top <n>, default is 10", "all/everyone - include bots"],
            example="10 #channel",
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "everyone"],
            help=MessagesScanner.help(),
            intro_context="Messages",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        self.all_messages = "all" in args or "everyone" in args
        # Create mentions dict
        self.messages = defaultdict(Counter)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return MessagesScanner.analyse_message(
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
                mention(name),
                total_usage=usage_count,
                counted="message",
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
        *,
        all_messages: bool,
    ) -> bool:
        impacted = False
        if (
            len(raw_members) == 0
            and (not message.bot or all_messages)
            or message.author in raw_members
        ):
            impacted = True
            messages[message.author].update_use(1, message.created_at, channel_id)
        return impacted
