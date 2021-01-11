from typing import List
import discord


# Custom libs

from .scanner import Scanner
from data_types import Composition
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
        self.comp = Composition()
        return True

    def compute_message(self, channel: ChannelLogs, message: MessageLog):
        return Composition.analyse_message(message, self.comp, self.raw_members)

    def get_results(self, intro: str) -> List[str]:
        Composition.compute_results(self.comp)
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
            pass  # TODO
        return impacted

    @staticmethod
    def compute_results(comp: Composition):
        pass  # TODO
