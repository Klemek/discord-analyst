from typing import Dict, List
from collections import defaultdict
import discord
import re

# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import (
    COMMON_HELP_ARGS,
    plural,
    precise,
)


class WordsScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%words: Rank words by their usage\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* <n> - top <n> words, default is 10\n"
            + "* everyone - include bots\n"
            + "Example: %words 10 #mychannel1 #mychannel2 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "everyone"],
            help=WordsScanner.help(),
            intro_context="Words usage",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        self.words = defaultdict(Counter)
        self.all_messages = "all" in args or "everyone" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return WordsScanner.analyse_message(
            message,
            self.words,
            self.raw_members,
            all_messages=self.all_messages,
        )

    def get_results(self, intro: str) -> List[str]:
        words = [word for word in self.words]
        words.sort(key=lambda word: self.words[word].score(), reverse=True)
        words = words[: self.top]
        # Get the total of all emotes used
        usage_count = Counter.total(self.words)
        print(len(self.words))
        res = [intro]
        res += [
            self.words[word].to_string(
                words.index(word),
                f"`{word}`",
                total_usage=usage_count,
            )
            for word in words
        ]
        res += [
            f"Total: {plural(usage_count,'time')} ({precise(usage_count/self.msg_count)}/msg)"
        ]
        return res

    special_cases = ["'s", "s"]

    @staticmethod
    def analyse_message(
        message: MessageLog,
        words: Dict[str, Counter],
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
        ):
            impacted = True
            for word in re.split("[^\w\-']", message.content):
                m = re.match("[^\w]*((?![\d_])\w.+(?![\d_])\w)[^\w]*", word)
                if m:
                    word = m[1].lower()
                    for case in WordsScanner.special_cases:
                        if word.endswith(case) and word[: -len(case)] in words:
                            word = word[: -len(case)]
                            break
                        if word + case in words:
                            words[word] = words[word + case]
                            del words[word + case]
                            break
                    words[word].update_use(
                        message.content.count(word), message.created_at
                    )
        return impacted
