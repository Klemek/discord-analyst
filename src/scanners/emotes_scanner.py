from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from data_types import Emote, get_emote_dict
from .scanner import Scanner
from utils import emojis, COMMON_HELP_ARGS, plural, precise


class EmotesScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%emojis: Rank emojis by their usage\n"
            + "arguments:\n"
            + COMMON_HELP_ARGS
            + "* <n> - top <n> emojis, default is 20\n"
            + "* all - list all common emojis in addition to this guild's\n"
            + "* members - show top member for each emojis\n"
            + "* sort:usage/reaction - other sorting methods\n"
            + "* everyone - include bots\n"
            + "Example: %emojis 10 all #mychannel1 #mychannel2 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "members", "sort:usage", "sort:reaction", "everyone"],
            help=EmotesScanner.help(),
            intro_context="Emoji usage",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        guild = message.channel.guild
        # get max emotes to view
        self.top = 20
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        # check other args
        self.all_emojis = "all" in args
        self.show_members = "members" in args and (
            len(self.members) == 0 or len(self.members) > 1
        )
        # Create emotes dict from custom emojis of the guild
        self.emotes = get_emote_dict(guild)
        self.sort = None
        if "sort:usage" in args:
            self.sort = "usage"
        elif "sort:reaction" in args:
            self.sort = "reaction"
        self.all_messages = "everyone" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return EmotesScanner.analyse_message(
            message,
            self.emotes,
            self.raw_members,
            all_emojis=self.all_emojis,
            all_messages=self.all_messages,
        )

    def get_results(self, intro: str) -> List[str]:
        names = [name for name in self.emotes]
        names.sort(
            key=lambda name: self.emotes[name].score(
                usage_weight=(0 if self.sort == "reaction" else 1),
                react_weight=(0 if self.sort == "usage" else 1),
            ),
            reverse=True,
        )
        names = names[: self.top]
        # Get the total of all emotes used
        usage_count = 0
        reaction_count = 0
        for name in self.emotes:
            usage_count += self.emotes[name].usages
            reaction_count += self.emotes[name].reactions
        res = [intro]
        allow_unused = self.full and len(self.members) == 0
        if self.sort is not None:
            res += [f"(Sorted by {self.sort})"]
        res += [
            self.emotes[name].to_string(
                names.index(name),
                name,
                total_usage=usage_count,
                total_react=reaction_count,
                show_life=False,
                show_members=self.show_members or len(self.raw_members) == 0,
            )
            for name in names
            if allow_unused or self.emotes[name].used()
        ]
        res += [
            f"Total: {plural(usage_count,'time')} ({precise(usage_count/self.msg_count)}/msg)"
        ]
        if reaction_count > 0:
            res[-1] += f" and {plural(reaction_count, 'reaction')}"
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog,
        emotes: Dict[str, Emote],
        raw_members: List[int],
        *,
        all_emojis: bool,
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
            # Find all emotes un the current message in the form "<:emoji:123456789>"
            # Filter for known emotes
            found = emojis.regex.findall(message.content)
            # For each emote, update its usage
            for name in found:
                if name not in emotes:
                    if not all_emojis or name not in emojis.unicode_list:
                        continue
                emotes[name].usages += 1
                emotes[name].update_use(message.created_at, [message.author])
        # For each reaction of this message, test if known emote and update when it's the case
        for name in message.reactions:
            if name not in emotes:
                if not all_emojis or name not in emojis.unicode_list:
                    continue
            if len(raw_members) == 0:
                emotes[name].reactions += len(message.reactions[name])
                emotes[name].update_use(message.created_at, message.reactions[name])
            else:
                for member in raw_members:
                    if member in message.reactions[name]:
                        emotes[name].reactions += 1
                        emotes[name].update_use(message.created_at, [member])
        return impacted
