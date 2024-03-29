from typing import Dict, List
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from data_types import Emoji, get_emoji_dict
from .scanner import Scanner
from utils import emojis, generate_help, plural, precise


class EmojisScanner(Scanner):
    @staticmethod
    def help() -> str:
        return generate_help(
            "emojis",
            "Rank emojis by their usage",
            args=[
                "<n> - top <n> emojis, default is 20",
                "all - list all common emojis in addition to this guild's",
                "members - show top member for each emojis",
                "sort:usage/reaction - other sorting methods",
                "everyone - include bots",
            ],
            example="10 all #mychannel1 #mychannel2 @user",
        )

    def __init__(self):
        super().__init__(
            has_digit_args=True,
            valid_args=["all", "members", "sort:usage", "sort:reaction", "everyone"],
            help=EmojisScanner.help(),
            intro_context="Emoji usage",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        guild = message.channel.guild
        # get max emojis to view
        self.top = 20
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        # check other args
        self.all_emojis = "all" in args
        self.show_members = "members" in args and (
            len(self.members) == 0 or len(self.members) > 1
        )
        # Create emojis dict from custom emojis of the guild
        self.emojis = get_emoji_dict(guild)
        self.sort = None
        if "sort:usage" in args:
            self.sort = "usage"
        elif "sort:reaction" in args:
            self.sort = "reaction"
        self.all_messages = "everyone" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return EmojisScanner.analyse_message(
            message,
            self.emojis,
            self.raw_members,
            all_emojis=self.all_emojis,
            all_messages=self.all_messages,
        )

    def get_results(self, intro: str) -> List[str]:
        names = [name for name in self.emojis]
        names.sort(
            key=lambda name: self.emojis[name].score(
                usage_weight=(0 if self.sort == "reaction" else 1),
                react_weight=(0 if self.sort == "usage" else 1),
            ),
            reverse=True,
        )
        names = names[: self.top]
        # Get the total of all emojis used
        usage_count = 0
        reaction_count = 0
        for name in self.emojis:
            usage_count += self.emojis[name].usages
            reaction_count += self.emojis[name].reactions
        res = [intro]
        allow_unused = self.full and len(self.members) == 0
        if self.sort is not None:
            res += [f"(Sorted by {self.sort})"]
        res += [
            self.emojis[name].to_string(
                names.index(name),
                name,
                total_usage=usage_count,
                total_react=reaction_count,
                show_life=False,
                show_members=self.show_members or len(self.raw_members) == 0,
            )
            for name in names
            if allow_unused or self.emojis[name].used()
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
        emojis_dict: Dict[str, Emoji],
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
            # Find all emojis un the current message in the form "<:emoji:123456789>"
            # Filter for known emojis
            found = emojis.regex.findall(message.content)
            # For each emoji, update its usage
            for name in found:
                if name not in emojis_dict:
                    if not all_emojis or name not in emojis.unicode_list:
                        continue
                emojis_dict[name].usages += 1
                emojis_dict[name].update_use(message.created_at, [message.author])
        # For each reaction of this message, test if known emoji and update when it's the case
        for name in message.reactions:
            if name not in emojis_dict:
                if not all_emojis or name not in emojis.unicode_list:
                    continue
            if len(raw_members) == 0:
                emojis_dict[name].reactions += len(message.reactions[name])
                emojis_dict[name].update_use(
                    message.created_at, message.reactions[name]
                )
            else:
                for member in raw_members:
                    if member in message.reactions[name]:
                        emojis_dict[name].reactions += 1
                        emojis_dict[name].update_use(message.created_at, [member])
        return impacted
