from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import discord
import re

# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import (
    generate_help,
    plural,
    precise,
    mention,
    escape_text,
)


class FindScanner(Scanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "find",
            "Find specific words or phrases (you can use quotes to add spaces in queries, backticks define regexes)",
            args=[
                "top - rank users for these queries",
                "all/everyone - include bots",
            ],
            example='#mychannel1 #mychannel2 @user "I love you" "you too"',
        )

    def __init__(self):
        super().__init__(
            all_args=True,
            valid_args=["all", "everyone", "top"],
            help=FindScanner.help(),
            intro_context="Matches",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.matches = defaultdict(Counter)
        self.all_messages = "all" in args or "everyone" in args
        self.top = "top" in args or len(self.other_args) == 1
        if len(self.other_args) == 0:
            await message.channel.send(
                "You need to add a query to find (you can use quotes to add spaces in queries, backticks define regexes)",
                reference=message,
            )
            return False
        self.queries = [
            (query, query.strip("`") if re.match(r"^`.*`$", query) else None)
            for query in self.other_args
        ]
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return FindScanner.analyse_message(
            message,
            self.matches,
            self.queries,
            self.raw_members,
            all_messages=self.all_messages,
            top=self.top,
        )

    def get_results(self, intro: str) -> List[str]:
        res = [intro]
        matches = [match for match in self.matches]
        matches.sort(key=lambda match: self.matches[match].score(), reverse=True)
        usage_count = Counter.total(self.matches)
        if self.top:
            res += [
                self.matches[match].to_string(
                    matches.index(match),
                    mention(match),
                    total_usage=usage_count,
                )
                for match in matches
            ]
        else:
            res += [
                self.matches[match].to_string(
                    matches.index(match),
                    f'"{escape_text(match)}"'
                    if len(match.strip("`")) == len(match)
                    else match,
                    total_usage=self.msg_count,
                    ranking=False,
                    transform=lambda id: f" by {mention(id)}",
                    top=len(self.members) != 1,
                )
                for match in matches
            ]
        if self.top or len(matches) > 1:
            res += [
                f"Total: {plural(usage_count,'time')} ({precise(usage_count/self.msg_count)}/msg)"
            ]
        return res

    special_cases = ["'s", "s"]

    @staticmethod
    def analyse_message(
        message: MessageLog,
        matches: Dict[str, Counter],
        queries: List[Tuple[str, Optional[str]]],
        raw_members: List[int],
        *,
        all_messages: bool,
        top: bool,
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if (
            (not message.bot or all_messages)
            and len(raw_members) == 0
            or message.author in raw_members
        ):
            impacted = True
            content = message.content.lower()
            for query in queries:
                if query[1] is not None:
                    count = len(re.findall(query[1], message.content))
                else:
                    count = content.count(query[0].lower())
                if top:
                    if count > 0:
                        matches[message.author].update_use(count, message.created_at)
                else:
                    matches[query[0]].update_use(
                        count, message.created_at, message.author
                    )
        return impacted
