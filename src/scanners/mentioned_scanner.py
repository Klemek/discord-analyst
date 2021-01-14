from typing import Dict, List
from collections import defaultdict
import discord


# Custom libs

from logs import ChannelLogs, MessageLog
from .scanner import Scanner
from data_types import Counter
from utils import COMMON_HELP_ARGS, plural, precise, mention, alt_mention


class MentionedScanner(Scanner):
    @staticmethod
    def help() -> str:
        return (
            "```\n"
            + "%mentioned: Rank specific user's mentions by their usage\n"
            + "arguments:\n"
            + "* @member/me - (required) one or more member\n"
            + "\n".join(COMMON_HELP_ARGS.split("\n")[1:])
            + "* <n> - top <n> mentions, default is 10\n"
            + "* all - include bots mentions\n"
            + "Example: %mentioned 10 @user\n"
            + "```"
        )

    def __init__(self):
        super().__init__(
            valid_args=["all"],
            help=MentionedScanner.help(),
            intro_context="Mentioned by members",
        )
        self.top = 10

    async def init(self, message: discord.Message, *args: str) -> bool:
        # get max emotes to view
        self.top = 10
        for arg in args:
            if arg.isdigit():
                self.top = int(arg)
        if len(self.members) == 0:
            await message.channel.send(
                "You need to mention at least one member or use `me`", reference=message
            )
            return False
        self.all_mentions = "all" in args
        # Create mentions dict
        self.mentions = defaultdict(Counter)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return MentionedScanner.analyse_message(
            message, self.mentions, self.raw_members, all_mentions=self.all_mentions
        )

    def get_results(self, intro: str) -> List[str]:
        names = [name for name in self.mentions]
        names.sort(key=lambda name: self.mentions[name].score(), reverse=True)
        names = names[: self.top]
        # Get the total of all emotes used
        usage_count = sum([mention.usages for mention in self.mentions.values()])
        res = [intro]
        res += [
            self.mentions[name].to_string(
                names.index(name),
                name,
                total_usage=usage_count,
            )
            for name in names
        ]
        res += [
            f"Total: {plural(usage_count,'time')} ({precise(usage_count/self.msg_count)}/msg)"
        ]
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog,
        mentions: Dict[str, Counter],
        raw_members: List[int],
        *,
        all_mentions: bool,
    ) -> bool:
        impacted = True
        if not message.bot or all_mentions:
            for member_id in message.mentions:
                if member_id in raw_members:
                    count = message.content.count(
                        mention(member_id)
                    ) + message.content.count(alt_mention(member_id))
                    mentions[mention(message.author)].update_use(
                        count, message.created_at
                    )
        return impacted
