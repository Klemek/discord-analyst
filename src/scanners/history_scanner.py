from abc import ABC, abstractmethod
from typing import List
import discord

# Custom libs

from .scanner import Scanner
from data_types import History
from logs import ChannelLogs, MessageLog
from utils import COMMON_HELP_ARGS


class HistoryScanner(Scanner, ABC):
    @staticmethod
    def help(*, cmd: str, text: str) -> str:
        return (
            "```\n"
            + f"%{cmd}: {text}\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* all/everyone - include bots\n"
            + "Example: %{cmd} #mychannel1 @user\n"
            + "```"
        )

    def __init__(self, *, help: str):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "everyone"],
            help=help,
            intro_context="",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.history = History()
        self.all_messages = "all" in args or "everyone" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return HistoryScanner.analyse_message(
            channel,
            message,
            self.history,
            self.raw_members,
            all_messages=self.all_messages,
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
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if (
            (not message.bot or all_messages)
            and len(raw_members) == 0
            or message.author in raw_members
        ) and (message.content or message.attachment):
            impacted = True
            history.messages += [message]
        return impacted
