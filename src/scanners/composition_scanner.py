from typing import List, Dict
from collections import defaultdict
import discord


# Custom libs

from .scanner import Scanner
from . import EmotesScanner
from data_types import Composition, Emote, get_emote_dict
from logs import ChannelLogs, MessageLog


class CompositionScanner(Scanner):
    @staticmethod
    def help() -> str:
        return "```\n"
        +"%comp : Show composition statistics\n"
        +"arguments:\n"
        +"* @member : filter for one or more member\n"
        +"* #channel : filter for one or more channel\n"
        +"Example: %comp #mychannel1 @user\n"
        +"```"

    def __init__(self):
        super().__init__(
            help=CompositionScanner.help(),
            intro_context="Composition",
        )

    async def init(self, message: discord.Message, *args: str) -> bool:
        guild = message.channel.guild
        self.comp = Composition()
        # Create emotes dict from custom emojis of the guild
        self.emotes = get_emote_dict(message.channel.guild)
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        ret = CompositionScanner.analyse_message(message, self.comp, self.raw_members)
        ret &= EmotesScanner.analyse_message(
            message, self.emotes, self.raw_members, all_emojis=True
        )
        return ret

    def get_results(self, intro: str) -> List[str]:
        CompositionScanner.compute_results(self.comp, self.emotes)
        res = [intro]
        res += self.comp.to_string()
        return res

    @staticmethod
    def analyse_message(
        message: MessageLog, comp: Composition, raw_members: List[int]
    ) -> bool:
        impacted = False
        # If author is included in the selection (empty list is all)
        if len(raw_members) == 0 or message.author in raw_members:
            impacted = True
            pass  # TODO
        return impacted

    @staticmethod
    def compute_results(comp: Composition, emotes: Dict[str, Emote]):
        pass  # TODO
