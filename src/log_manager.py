from typing import Union, List, Tuple
import os
import discord
import json
import gzip
from datetime import datetime
import logging

from utils import code_message, is_extension

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)


CHUNK_SIZE = 1000
FORMAT = 3
IMAGE_FORMAT = ["gif", "gifv", "png", "jpg", "jpeg", "bmp"]
EMBED_IMAGES = ["image", "gifv"]

current_analysis = []


class FakeMessage:
    def __init__(self, id: int):
        self.id = id


class MessageLog:
    def __init__(self, message: Union[discord.Message, dict]):
        if isinstance(message, discord.Message):
            self.id = message.id
            self.created_at = message.created_at
            self.edited_at = message.edited_at
            self.author = message.author.id
            self.pinned = message.pinned
            self.mention_everyone = message.mention_everyone
            self.tts = message.tts
            self.reference = (
                message.reference.message_id if message.reference is not None else None
            )
            self.bot = message.author.bot or message.author.system
            self.content = message.content
            self.mentions = message.raw_mentions
            self.role_mentions = message.raw_role_mentions
            self.channel_mentions = message.raw_channel_mentions
            self.image = False
            for attachment in message.attachments:
                if is_extension(attachment.filename, IMAGE_FORMAT):
                    self.image = True
                    break
            if not self.image:
                for embed in message.embeds:
                    if embed.type in EMBED_IMAGES:
                        self.image = True
                        break
            self.reactions = {}
        elif isinstance(message, dict):
            self.id = int(message["id"])
            self.created_at = datetime.fromisoformat(message["created_at"])
            self.edited_at = (
                datetime.fromisoformat(message["edited_at"])
                if message["edited_at"] is not None
                else None
            )
            self.author = int(message["author"])
            self.pinned = message["pinned"]
            self.mention_everyone = message["mention_everyone"]
            self.tts = message["tts"]
            self.reference = (
                int(message["reference"]) if message["reference"] is not None else None
            )
            self.bot = message["bot"]
            self.content = message["content"]
            self.mentions = [int(m) for m in message["mentions"]]
            self.role_mentions = [int(m) for m in message["role_mentions"]]
            self.channel_mentions = [int(m) for m in message["channel_mentions"]]
            self.image = message["image"]
            self.reactions = message["reactions"]

    async def load(self, message: discord.Message):
        for reaction in message.reactions:
            self.reactions[str(reaction.emoji)] = []
            async for user in reaction.users():
                self.reactions[str(reaction.emoji)] += [user.id]

    def dict(self) -> dict:
        message = dict(self.__dict__)
        message["created_at"] = self.created_at.isoformat()
        message["edited_at"] = (
            self.edited_at.isoformat() if self.edited_at is not None else None
        )
        return message


class ChannelLogs:
    def __init__(self, channel: Union[discord.TextChannel, dict]):
        if isinstance(channel, discord.TextChannel):
            self.id = channel.id
            self.name = channel.name
            self.last_message_id = None
            self.format = FORMAT
            self.messages = []
        elif isinstance(channel, dict):
            self.format = channel["format"] if "format" in channel else None
            if self.format != FORMAT:
                return
            self.id = int(channel["id"])
            self.name = channel["name"]
            self.last_message_id = int(channel["last_message_id"])
            self.messages = [MessageLog(message) for message in channel["messages"]]

    async def load(self, channel: discord.TextChannel) -> Tuple[int, int]:
        self.name = channel.name
        self.channel = channel
        try:
            if self.last_message_id is not None:  # append
                while self.last_message_id != channel.last_message_id:
                    async for message in channel.history(
                        limit=CHUNK_SIZE,
                        after=FakeMessage(self.last_message_id),
                        oldest_first=True,
                    ):
                        self.last_message_id = message.id
                        m = MessageLog(message)
                        await m.load(message)
                        self.messages.insert(0, m)
                    yield len(self.messages), False
            else:  # first load
                last_message_id = None
                done = 0
                while done >= CHUNK_SIZE or last_message_id is None:
                    done = 0
                    async for message in channel.history(
                        limit=CHUNK_SIZE,
                        before=FakeMessage(last_message_id)
                        if last_message_id is not None
                        else None,
                        oldest_first=False,
                    ):
                        done += 1
                        last_message_id = message.id
                        m = MessageLog(message)
                        await m.load(message)
                        self.messages += [m]
                    yield len(self.messages), False
                self.last_message_id = channel.last_message_id
        except discord.errors.HTTPException:
            return  # When an exception occurs (like Forbidden)
        yield len(self.messages), True

    def dict(self) -> dict:
        channel = dict(self.__dict__)
        channel.pop("channel", None)
        channel["messages"] = [message.dict() for message in self.messages]
        return channel


class GuildLogs:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.log_file = os.path.join(LOG_DIR, f"{guild.id}.logz")
        self.channels = {}

    def dict(self) -> dict:
        return {id: self.channels[id].dict() for id in self.channels}

    async def load(
        self, progress: discord.Message, target_channels: List[discord.TextChannel] = []
    ) -> Tuple[int, int]:
        global current_analysis
        if self.log_file in current_analysis:
            return -1, -1
        current_analysis += [self.log_file]
        # read logs
        t0 = datetime.now()
        if os.path.exists(self.log_file):
            channels = {}
            try:
                gziped_data = None
                await code_message(progress, "Reading saved history (1/4)...")
                with open(self.log_file, mode="rb") as f:
                    gziped_data = f.read()
                await code_message(progress, "Reading saved history (2/4)...")
                json_data = gzip.decompress(gziped_data)
                await code_message(progress, "Reading saved history (3/4)...")
                channels = json.loads(json_data)
                await code_message(progress, "Reading saved history (4/4)...")
                self.channels = {int(id): ChannelLogs(channels[id]) for id in channels}
                # remove invalid format
                self.channels = {
                    id: self.channels[id]
                    for id in self.channels
                    if self.channels[id].format == FORMAT
                }
                dt = (datetime.now() - t0).total_seconds()
                logging.info(f"log {self.guild.id} > loaded in {dt} s")
            except json.decoder.JSONDecodeError:
                logging.error(f"log {self.guild.id} > invalid JSON")
            except IOError:
                logging.error(f"log {self.guild.id} > cannot read")
        # load channels
        t0 = datetime.now()
        if len(target_channels) == 0:
            target_channels = self.guild.text_channels
        loading_new = 0
        total_msg = 0
        queried_msg = 0
        total_chan = 0
        max_chan = len(target_channels)
        await code_message(
            progress,
            f"Reading history...\n0 messages in 0/{max_chan} channels\n(this might take a while)",
        )
        for channel in target_channels:
            if channel.id not in self.channels:
                loading_new += 1
                self.channels[channel.id] = ChannelLogs(channel)
            start_msg = len(self.channels[channel.id].messages)
            async for count, done in self.channels[channel.id].load(channel):
                if count > 0:
                    tmp_queried_msg = queried_msg + count - start_msg
                    tmp_msg = total_msg + count
                    warning_msg = "(this might take a while)"
                    if len(target_channels) > 5 and loading_new > 5:
                        warning_msg = (
                            "(most channels are new, this might take a looong while)"
                        )
                    elif loading_new > 0:
                        warning_msg = (
                            "(some channels are new, this might take a long while)"
                        )
                    dt = (datetime.now() - t0).total_seconds()
                    await code_message(
                        progress,
                        f"Reading history...\n{tmp_msg:,} messages in {total_chan + 1}/{max_chan} channels ({round(tmp_queried_msg/dt)}m/s)\n{warning_msg}",
                    )
                    if done:
                        total_chan += 1
            total_msg += len(self.channels[channel.id].messages)
            queried_msg += count - start_msg
        dt = (datetime.now() - t0).total_seconds()
        logging.info(
            f"log {self.guild.id} > queried in {dt} s -> {queried_msg / dt} m/s"
        )
        # write logs
        t0 = datetime.now()
        await code_message(
            progress,
            f"Saving (1/3)...\n{total_msg:,} messages in {total_chan} channels",
        )
        json_data = bytes(json.dumps(self.dict()), "utf-8")
        await code_message(
            progress,
            f"Saving (2/3)...\n{total_msg:,} messages in {total_chan} channels",
        )
        gziped_data = gzip.compress(json_data)
        await code_message(
            progress,
            f"Saving (3/3)...\n{total_msg:,} messages in {total_chan} channels",
        )
        with open(self.log_file, mode="wb") as f:
            f.write(gziped_data)
        dt = (datetime.now() - t0).total_seconds()
        logging.info(f"log {self.guild.id} > written in {dt} s")
        await code_message(
            progress, f"Analysing...\n{total_msg:,} messages in {total_chan} channels"
        )
        current_analysis.remove(self.log_file)
        return total_msg, total_chan
