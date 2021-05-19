from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import discord
import re

# Custom libs

from .scanner import Scanner
from data_types import History
from logs import ChannelLogs, MessageLog


class HistoryScanner(Scanner, ABC):
    def __init__(self, *, help: str):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "everyone"],
            help=help,
            intro_context="",
            all_args=True,
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.history = History()
        self.all_messages = "all" in args or "everyone" in args
        self.images_only = "image" in args
        if not self.images_only:
            self.queries = [
                (
                    query.lower(),
                    query.strip("`") if re.match(r"^`.*`$", query) else None,
                )
                for query in self.other_args
            ]
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
            queries=self.queries,
            images_only=self.images_only,
        )

    @abstractmethod
    def get_results(self, intro: str):
        pass

    @staticmethod
    def analyse_message(
        channel: ChannelLogs,
        message: MessageLog,
        history: History,
        raw_members: List[int],
        *,
        all_messages: bool,
        queries: List[Tuple[str, Optional[str]]],
        images_only: bool,
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
            and (not images_only or message.image)
        ):
            content = message.content.lower()
            for query in queries:
                if query[1] is not None:
                    if not re.match(query[1], message.content):
                        return False
                elif not query[0] in content:
                    return False
            impacted = True
            history.messages += [message]
        return impacted
