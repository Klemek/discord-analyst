from abc import ABC, abstractmethod
from typing import Callable, List
import discord
import re

# Custom libs

from .scanner import Scanner
from data_types import History
from logs import ChannelLogs, MessageLog


class HistoryScanner(Scanner, ABC):
    def __init__(self, *, help: str, valid_args: List[str] = [], allow_queries: bool = False):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "everyone"] + valid_args,
            help=help,
            intro_context="",
            all_args=allow_queries,
        )
        self.allow_queries = allow_queries

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.history = History()
        self.all_messages = "all" in args or "everyone" in args
        if self.allow_queries:
            self.queries = [(query.lower(), query.strip("`") if re.match(r"^`.*`$", query) else None) for query in self.other_args]
        else:
            self.queries = []
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return HistoryScanner.analyse_message(
            channel,
            message,
            self.history,
            self.raw_members,
            all_messages=self.all_messages,
            allow_message=lambda *args: self.allow_message(*args) and self.allow_message_query(*args),
        )

    @abstractmethod
    def get_results(self, intro: str):
        pass

    @abstractmethod
    def allow_message(self, channel: ChannelLogs, message: MessageLog) -> bool:
        pass

    def allow_message_query(self, channel: ChannelLogs, message: MessageLog) -> bool:
        if not self.allow_queries or len(self.queries) == 0:
            return True
        else:
            content = message.content.lower()
            for query in self.queries:
                if query[1] is not None:
                    if not re.match(query[1], message.content):
                        return False
                elif not query[0] in content:
                    return False
        return True

    @staticmethod
    def analyse_message(
        channel: ChannelLogs,
        message: MessageLog,
        history: History,
        raw_members: List[int],
        *,
        all_messages: bool,
        allow_message: Callable
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if (
            (
                (not message.bot or all_messages)
                and len(raw_members) == 0
                or message.author in raw_members
            )
            and (message.content or message.attachment)
            and allow_message(channel, message)
        ):
            impacted = True
            history.messages += [message]
        return impacted
