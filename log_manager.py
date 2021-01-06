from typing import Union, List, Tuple
import os
import discord
import json
from datetime import datetime
import logging

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)


CHUNK_SIZE = 1000


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
                message.reference.id if message.reference is not None else None
            )
            self.content = message.content
            self.mentions = message.raw_mentions
            self.role_mentions = message.raw_role_mentions
            self.channel_mentions = message.raw_channel_mentions
            self.reactions = {}
        elif isinstance(message, dict):
            self.id = int(message["id"])
            self.created_at = datetime.fromisoformat(message["created_at"])
            self.edited_at = (
                datetime.fromisoformat(message["edited_at"])
                if message["edited_at"] is not None
                else None
            )
            self.author = message["author"]
            self.pinned = message["pinned"]
            self.mention_everyone = message["mention_everyone"]
            self.tts = message["tts"]
            self.reference = message["reference"]
            self.content = message["content"]
            self.mentions = message["mentions"]
            self.role_mentions = message["role_mentions"]
            self.channel_mentions = message["channel_mentions"]
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
            self.messages = []
        elif isinstance(channel, dict):
            self.id = int(channel["id"])
            self.name = channel["name"]
            self.last_message_id = channel["last_message_id"]
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
                        if not message.author.bot:
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
                        if not message.author.bot:
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
    ):
        await progress.edit(
            content=f"```Reading history...\n(this might take a while)```"
        )
        # read logs
        t0 = datetime.now()
        if os.path.exists(self.log_file):
            channels = {}
            try:
                with open(self.log_file, mode="r") as f:
                    channels = json.loads(f.readline().strip())
                self.channels = {int(id): ChannelLogs(channels[id]) for id in channels}
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
        total_chan = 0
        for channel in target_channels:
            if channel.id not in self.channels:
                loading_new += 1
                self.channels[channel.id] = ChannelLogs(channel)
            async for count, done in self.channels[channel.id].load(channel):
                if count > 0:
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
                    await progress.edit(
                        content=f"```Reading history...\n{tmp_msg} messages in {total_chan + 1} channels ({round(tmp_msg/dt)}m/s)\n{warning_msg}```"
                    )
                    if done:
                        total_chan += 1
            total_msg += len(self.channels[channel.id].messages)
        dt = (datetime.now() - t0).total_seconds()
        await progress.edit(
            content=f"```Analysing...\n{tmp_msg} messages in {total_chan} channels```"
        )
        logging.info(f"log {self.guild.id} > queried in {dt} s -> {total_msg / dt} m/s")
        # write logs
        t0 = datetime.now()
        with open(self.log_file, mode="w") as f:
            f.write(json.dumps(self.dict()))
        dt = (datetime.now() - t0).total_seconds()
        logging.info(f"log {self.guild.id} > written in {dt} s")
        return total_msg, total_chan
