from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
import logging
import re
import discord
import inspect


from utils import (
    no_duplicate,
    get_intro,
    delta,
    gdpr,
    ISO8601_REGEX,
    RELATIVE_REGEX,
    parse_time,
    command_cache,
    FilterLevel,
    SPLIT_TOKEN,
)
from logs import (
    GuildLogs,
    ChannelLogs,
    MessageLog,
    ALREADY_RUNNING,
    CANCELLED,
    NO_FILE,
)


class Scanner(ABC):
    VALID_ARGS = [
        "me",
        "here",
        "fast",
        "fresh",
        "mobile",
        "mention",
        "nsfw",
        "nsfw:allow",
        "nsfw:only",
    ]

    def __init__(
        self,
        *,
        has_digit_args: bool = False,
        valid_args: List[str] = [],
        help: str,
        intro_context: str,
        all_args: bool = False,
    ):
        self.has_digit_args = has_digit_args
        self.valid_args = valid_args
        self.all_args = all_args
        self.help = help
        self.intro_context = intro_context

        self.other_args = []

        self.members = []
        self.raw_members = []
        self.full = False
        self.channels = []

        self.msg_count = 0
        self.chan_count = 0

    async def compute(
        self,
        client: discord.client,
        message: discord.Message,
        *args: str,
        other_mentions: List[str] = [],
    ):
        args = list(args)
        guild = message.guild
        progress = None
        try:
            with GuildLogs(guild) as logs:
                # If "%cmd help" redirect to "%help cmd"
                if len(args) > 1 and args[1] == "help":
                    await client.bot.help(client, message, "help", args[0])
                    return

                # check args validity
                str_channel_mentions = [
                    str(channel.id) for channel in message.channel_mentions
                ]
                str_mentions = [str(member.id) for member in message.mentions]
                dates = []
                for i, arg in enumerate(args[1:]):
                    skip_check = False
                    if self.all_args and f"'{arg}'" in message.content or f"\"{arg}\"" in message.content:
                        self.other_args += [arg]
                    elif re.match(r"^<@!?\d+>$", arg):
                        arg = arg[3:-1] if "!" in arg else arg[2:-1]
                    elif re.match(r"^<#!?\d+>$", arg):
                        arg = arg[3:-1] if "!" in arg else arg[2:-1]
                    elif re.match(ISO8601_REGEX, arg) or re.match(RELATIVE_REGEX, arg):
                        dates += [parse_time(arg)]
                        skip_check = True
                        if len(dates) > 2:
                            await message.channel.send(
                                f"Too many date arguments: `{arg}`", reference=message
                            )
                            return
                    if (
                        arg not in self.valid_args + Scanner.VALID_ARGS
                        and (not arg.isdigit() or not self.has_digit_args)
                        and arg not in str_channel_mentions
                        and arg not in str_mentions
                        and arg not in other_mentions
                        and not skip_check
                        and len(arg) > 0
                    ):
                        if self.all_args:
                            self.other_args += [arg]
                        else:
                            await message.channel.send(
                                f"Unrecognized argument: `{arg}`", reference=message
                            )
                            return

                for arg in self.other_args:
                    args.remove(arg)

                self.start_date = None if len(dates) < 1 else min(dates)
                self.stop_date = None if len(dates) < 2 else max(dates)

                if self.start_date is not None and self.start_date > datetime.now():
                    await message.channel.send(
                        f"Start date is after today", reference=message
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

                self.mention_users = "mention" in args or "mobile" in args

                # nsfw filter
                if "nsfw" in args or "nsfw:allow" in args:
                    self.nsfw = FilterLevel.ALLOW
                elif "nsfw:only" in args:
                    self.nsfw = FilterLevel.ONLY
                else:
                    self.nsfw = FilterLevel.NONE

                # fix nsfw filter if channel specified
                if not self.full and any(channel.nsfw for channel in self.channels):
                    self.nsfw = FilterLevel.ALLOW
                elif all(channel.nsfw for channel in self.channels):
                    self.nsfw = FilterLevel.ONLY

                # filter nsfw channels
                if self.nsfw == FilterLevel.NONE:
                    self.channels = list(
                        filter(lambda channel: not channel.nsfw, self.channels)
                    )
                elif self.nsfw == FilterLevel.ONLY:
                    self.channels = list(
                        filter(lambda channel: channel.nsfw, self.channels)
                    )

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
                        progress,
                        self.channels,
                        self.start_date,
                        self.stop_date,
                        fast="fast" in args,
                        fresh="fresh" in args,
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
                    elif total_msg == NO_FILE:
                        await message.channel.send(gdpr.TEXT)
                    else:
                        if self.start_date is not None and len(logs.channels) > 0:
                            self.start_date = max(
                                self.start_date,
                                min(
                                    [
                                        logs.channels[channel.id].start_date
                                        for channel in self.channels
                                        if channel.id in logs.channels
                                        and logs.channels[channel.id].start_date
                                        is not None
                                    ]
                                ),
                            )
                            if self.stop_date is None:
                                self.stop_date = datetime.utcnow()

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
                                        if (
                                            self.start_date is None
                                            or message_log.created_at >= self.start_date
                                        )
                                        and (
                                            self.stop_date is None
                                            or message_log.created_at <= self.stop_date
                                        )
                                    ]
                                )
                                self.total_msg += len(channel_logs.messages)
                                self.msg_count += count
                                self.chan_count += 1 if count > 0 else 0
                        logging.info(f"scan {guild.id} > scanned in {delta(t0):,}ms")
                        if self.msg_count == 0:
                            await message.channel.send(
                                "There are no messages found matching the filters",
                                reference=message,
                            )
                        else:
                            await progress.edit(content="```Computing results...```")
                            # Display results
                            t0 = datetime.now()
                            intro = get_intro(
                                self.intro_context,
                                self.full,
                                self.channels,
                                self.members,
                                self.msg_count,
                                self.chan_count,
                                self.start_date,
                                self.stop_date,
                            )
                            if inspect.iscoroutinefunction(self.get_results):
                                results = await self.get_results(intro)
                            else:
                                results = self.get_results(intro)
                            logging.info(
                                f"scan {guild.id} > results in {delta(t0):,}ms"
                            )
                            response = ""
                            first = True
                            allowed_mentions = (
                                discord.AllowedMentions.all()
                                if self.mention_users
                                else discord.AllowedMentions.none()
                            )
                            for r in results:
                                if r:
                                    if isinstance(r, int) and r == SPLIT_TOKEN:
                                        await message.channel.send(
                                            response,
                                            reference=message if first else None,
                                            allowed_mentions=allowed_mentions,
                                        )
                                        first = False
                                        response = ""
                                    elif isinstance(r, str):
                                        if len(response + "\n" + r) > 2000:
                                            await message.channel.send(
                                                response,
                                                reference=message if first else None,
                                                allowed_mentions=allowed_mentions,
                                            )
                                            first = False
                                            response = ""
                                        response += "\n" + r
                            if len(response) > 0:
                                await message.channel.send(
                                    response,
                                    reference=message if first else None,
                                    allowed_mentions=allowed_mentions,
                                )
                            command_cache.cache(self, message, args)
                # Delete custom progress message
                await progress.delete()
        except Exception as error:
            logging.exception(error)
            await message.channel.send(
                "An unexpected error happened while computing your command, we're sorry for the inconvenience.",
                reference=message,
            )
            if progress is not None:
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
