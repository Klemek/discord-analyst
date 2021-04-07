from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
import logging
import re
import discord

from utils import no_duplicate, get_intro, delta
from logs import GuildLogs, ChannelLogs, MessageLog, ALREADY_RUNNING, CANCELLED


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
        args = list(args)
        guild = message.guild
        with GuildLogs(guild) as logs:
            # If "%cmd help" redirect to "%help cmd"
            if "help" in args:
                await client.bot.help(client, message, "help", args[0])
                return

            # check args validity
            str_channel_mentions = [
                str(channel.id) for channel in message.channel_mentions
            ]
            str_mentions = [str(member.id) for member in message.mentions]
            for i, arg in enumerate(args[1:]):
                if re.match(r"^<@!?\d+>$", arg):
                    arg = arg[3:-1] if "!" in arg else arg[2:-1]
                elif re.match(r"^<#!?\d+>$", arg):
                    arg = arg[3:-1] if "!" in arg else arg[2:-1]
                if (
                    arg not in self.valid_args + ["me", "here", "fast", "fresh"]
                    and (not arg.isdigit() or not self.has_digit_args)
                    and arg not in str_channel_mentions
                    and arg not in str_mentions
                ):
                    await message.channel.send(
                        f"Unrecognized argument: `{arg}`", reference=message
                    )
                    return

            # Get selected channels or all of them if no channel arguments
            self.channels = no_duplicate(message.channel_mentions)

            # transform the "here" arg
            if "here" in args:
                self.channels += [message.channel]

            self.full = len(self.channels) == 0
            if self.full:
                self.channels = guild.text_channels

            # Get selected members
            self.members = no_duplicate(message.mentions)
            self.raw_members = no_duplicate(message.raw_mentions)

            # transform the "me" arg
            if "me" in args:
                self.members += [message.author]
                self.raw_members += [message.author.id]

            if not await self.init(message, *args):
                return

            # Start computing data
            async with message.channel.typing():
                progress = await message.channel.send(
                    "```Starting analysis...```",
                    reference=message,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                total_msg, total_chan = await logs.load(
                    progress, self.channels, fast="fast" in args, fresh="fresh" in args
                )
                if total_msg == CANCELLED:
                    await message.channel.send(
                        "Operation cancelled by user",
                        reference=message,
                    )
                elif total_msg == ALREADY_RUNNING:
                    await message.channel.send(
                        "An analysis is already running on this server, please be patient.",
                        reference=message,
                    )
                else:
                    self.msg_count = 0
                    self.total_msg = 0
                    self.chan_count = 0
                    t0 = datetime.now()
                    for channel in self.channels:
                        if channel.id in logs.channels:
                            channel_logs = logs.channels[channel.id]
                            count = sum(
                                [
                                    self.compute_message(channel_logs, message_log)
                                    for message_log in channel_logs.messages
                                ]
                            )
                            self.total_msg += len(channel_logs.messages)
                            self.msg_count += count
                            self.chan_count += 1 if count > 0 else 0
                    logging.info(f"scan {guild.id} > scanned in {delta(t0):,}ms")
                    if self.total_msg == 0:
                        await message.channel.send(
                            "There are no messages found matching the filters",
                            reference=message,
                        )
                    else:
                        await progress.edit(content="```Computing results...```")
                        # Display results
                        t0 = datetime.now()
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
                        logging.info(f"scan {guild.id} > results in {delta(t0):,}ms")
                        response = ""
                        first = True
                        for r in results:
                            if len(response + "\n" + r) > 2000:
                                await message.channel.send(
                                    response,
                                    reference=message if first else None,
                                    allowed_mentions=discord.AllowedMentions.none(),
                                )
                                first = False
                                response = ""
                            response += "\n" + r
                        if len(response) > 0:
                            await message.channel.send(
                                response,
                                reference=message if first else None,
                                allowed_mentions=discord.AllowedMentions.none(),
                            )
                # Delete custom progress message
                await progress.delete()

    @abstractmethod
    async def init(self, message: discord.Message, *args: str) -> bool:
        pass

    @abstractmethod
    def compute_message(self, channel: ChannelLogs, message: MessageLog) -> bool:
        pass

    @abstractmethod
    def get_results(self, intro: str) -> List[str]:
        pass
