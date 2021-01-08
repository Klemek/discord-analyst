from abc import ABC, abstractmethod
from typing import List
import discord

from utils import no_duplicate, get_intro
from logs import GuildLogs, ChannelLogs, MessageLog


class Scanner(ABC):
    def __init__(
        self,
        *,
        has_digit_args: bool = False,
        valid_args: List[str] = [],
        help: str,
        intro_context: str,
    ):
        self.has_digit_args = has_digit_args
        self.valid_args = valid_args
        self.help = help
        self.intro_context = intro_context

        self.members = []
        self.raw_members = []
        self.full = False
        self.channels = []

        self.msg_count = 0
        self.chan_count = 0

    async def compute(
        self, client: discord.client, message: discord.Message, *args: str
    ):
        guild = message.guild
        logs = GuildLogs(guild)

        # If "%cmd help" redirect to "%help cmd"
        if "help" in args:
            await client.bot.help(client, message, "help", args[0])
            return

        # check args validity
        str_channel_mentions = [channel.mention for channel in message.channel_mentions]
        str_mentions = [member.mention for member in message.mentions]
        for arg in args[1:]:
            if (
                arg not in self.valid_args
                and (not arg.isdigit() or not self.has_digit_args)
                and arg not in str_channel_mentions
                and arg not in str_mentions
            ):
                await message.channel.send(
                    f"{message.author.mention} unrecognized argument: `{arg}`"
                )
                return

        # Get selected channels or all of them if no channel arguments
        self.channels = no_duplicate(message.channel_mentions)
        self.full = len(self.channels) == 0
        if self.full:
            self.channels = guild.text_channels

        # Get selected members
        self.members = no_duplicate(message.mentions)
        self.raw_members = no_duplicate(message.raw_mentions)

        if not await self.init(message, *args):
            return

        # Start computing data
        async with message.channel.typing():
            progress = await message.channel.send("```Starting analysis...```")
            total_msg, total_chan = await logs.load(progress, self.channels)
            if total_msg == -1:
                await message.channel.send(
                    f"{message.author.mention} An analysis is already running on this server, please be patient."
                )
            else:
                self.msg_count = 0
                self.chan_count = 0
                for channel in self.channels:
                    channel_logs = logs.channels[channel.id]
                    count = sum(
                        [
                            self.compute_message(channel_logs, message_log)
                            for message_log in channel_logs.messages
                        ]
                    )
                    self.msg_count += count
                    self.chan_count += 1 if count > 0 else 0
                await progress.edit(content="```Computing results...```")
                # Display results
                results = self.get_results(
                    get_intro(
                        self.intro_context,
                        self.full,
                        self.channels,
                        self.members,
                        self.msg_count,
                        self.chan_count,
                    )
                )
                response = ""
                for r in results:
                    if len(response + "\n" + r) > 2000:
                        await message.channel.send(response)
                        response = ""
                    response += "\n" + r
                if len(response) > 0:
                    await message.channel.send(response)
            # Delete custom progress message
            await progress.delete()

    @abstractmethod
    async def init(self, message: discord.Message, *args: str) -> bool:
        pass

    @abstractmethod
    def compute_message(self, channel: ChannelLogs, message: MessageLog) -> bool:
        pass

    @abstractmethod
    def get_results(self, intro: str):
        pass