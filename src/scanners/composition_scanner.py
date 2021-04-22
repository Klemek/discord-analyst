from typing import List
import re
import discord


# Custom libs

from .scanner import Scanner
from data_types import Composition
from logs import ChannelLogs, MessageLog
from utils import emojis, generate_help


class CompositionScanner(Scanner):
    @staticmethod
    def help() -> str:
        return generate_help("compo", "Show composition statistics")

    def __init__(self):
        super().__init__(
            valid_args=["all", "everyone"],
            help=CompositionScanner.help(),
            intro_context="Composition",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        self.compo = Composition()
        self.all_messages = "all" in args or "everyone" in args
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        ret = CompositionScanner.analyse_message(
            message, self.compo, self.raw_members, all_messages=self.all_messages
        )
        return ret

    def get_results(self, intro: str) -> List[str]:
        res = [intro]
        res += self.compo.to_string(self.msg_count)
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog,
        compo: Composition,
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
            compo.total_characters += len(message.content)

            emojis_found = emojis.regex.findall(message.content)
            without_emoji = message.content
            for name in emojis_found:
                if name in emojis.unicode_list or re.match(
                    r"(<a?:[\w\-\~]+:\d+>|:[\w\\-\~]+:)", name
                ):
                    compo.emojis[name] += 1
                    i = without_emoji.index(name)
                    without_emoji = without_emoji[:i] + without_emoji[i + len(name) :]
            if len(message.content.strip()) > 0 and len(without_emoji.strip()) == 0:
                compo.emoji_only += 1
            if len(emojis_found) > 0:
                compo.emoji_msg += 1

            links_found = re.findall(r"https?:\/\/", message.content)
            compo.links += len(links_found)
            if len(links_found) > 0:
                compo.link_msg += 1

            mentions = (
                len(message.mentions)
                + len(message.role_mentions)
                + len(message.channel_mentions)
            )
            if message.mention_everyone:
                compo.everyone += 1
                mentions += 1
            if mentions > 0:
                compo.mentions += mentions
                compo.mention_msg += 1

            spoilers_found = re.findall(r"\|\|[^|]+\|\|", message.content)
            if len(spoilers_found) > 0:
                compo.spoilers += 1

            if message.edited_at is not None:
                compo.edited += 1
            if message.reference is not None:
                compo.answers += 1
            if message.image:
                compo.images += 1
            if message.tts:
                compo.tts += 1

            if (
                len(emojis_found) == 0
                and message.reference is None
                and not message.image
                and len(message.mentions) == 0
                and len(message.role_mentions) == 0
                and len(message.channel_mentions) == 0
                and not message.tts
                and not message.mention_everyone
                and not message.embed
                and not message.attachment
            ):
                compo.plain_text += 1
        return impacted
