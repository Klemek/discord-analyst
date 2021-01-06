from typing import Union, List
import os
import discord
import json

LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)


CHUNK_SIZE = 1000


class MessageLog:
    def __init__(self, message: Union[discord.Message, dict]):
        if isinstance(message, discord.Message):
            self.id = message.id
            self.created_at = message.created_at
            self.edited_at = message.edited_at
            self.author = message.author
            self.pinned = message.pinned
            self.mention_everyone = message.mention_everyone
            self.tts = message.tts
            self.reference = message.reference.id
            self.content = message.content
            self.mentions = message.raw_mentions
            self.role_mentions = message.raw_role_mentions
            self.channel_mentions = message.raw_channel_mentions
            self.reactions = {}
        elif isinstance(message, dict):
            self.id = message["id"]
            self.created_at = message["created_at"]
            self.edited_at = message["edited_at"]
            self.author = message["author"]
            self.pinned = message["pinned"]
            self.mention_everyone = message["mention_everyone"]
            self.tts = message["tts"]
            self.reference = message["reference.id"]
            self.content = message["content"]
            self.mentions = message["raw_mentions"]
            self.role_mentions = message["raw_role_mentions"]
            self.channel_mentions = message["raw_channel_mentions"]
            self.reactions = message["reactions"]

    async def load(self, message: discord.Message):
        for reaction in message.reactions:
            self.reactions[str(reaction)] = []
            async for user in reaction.users():
                self.reactions[str(reaction)] += user.id

    def dict(self):
        return self.__dict__


class ChannelLog:
    def __init__(self, channel: Union[discord.TextChannel, dict]):
        if isinstance(channel, discord.TextChannel):
            self.id = channel.id
            self.name = channel.name
            self.last_message_id = None
            self.messages = []
        elif isinstance(channel, dict):
            self.id = channel["id"]
            self.name = channel["name"]
            self.last_message_id = channel["last_message_id"]
            self.messages = [MessageLog(message) for message in channel["messages"]]

    async def load(self, channel: discord.TextChannel):
        self.name = channel.name
        if self.last_message_id is not None:  # append
            while self.last_message_id != channel.last_message_id:
                async for message in channel.history(
                    limit=CHUNK_SIZE, after=self.last_message_id, oldest_first=True
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
                    limit=CHUNK_SIZE, after=self.last_message_id, oldest_first=False
                ):
                    done += 1
                    last_message_id = message.id
                    m = MessageLog(message)
                    await m.load(message)
                    self.messages += [m]
                yield len(self.messages), False
            self.last_message_id == channel.last_message_id
        yield len(self.messages), True

    def dict(self):
        tmp = self.__dict__
        tmp["messages"] = [message.dict() for message in self.messages]
        return tmp


class GuildLogs:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.log_file = os.path.join(LOG_DIR, f"{guild}.logz")
        self.channels = {}

    def dict(self):
        return {id: self.channels[id].dict() for id in self.channels}

    async def load(self, target_channels: List[discord.TextChannel] = []):
        # read logs
        if os.path.exists(self.log_file):
            channels = {}
            with open(self.log_file, mode="r") as f:
                channels = json.loads(f.readline().strip())
            self.channels = {id: ChannelLog(channels[id]) for id in channels}
        # load channels
        if len(target_channels) == 0:
            target_channels = self.guild.text_channels
        loading_new = False
        total_msg = 0
        total_chan = 0
        for channel in target_channels:
            if channel.id not in self.channels:
                loading_new = True
                self.channels[channel.id] = ChannelLog(channel)
            async for count, done in self.channels[channel.id].load(channel):
                yield (
                    total_msg + count,
                    total_chan + (1 if done else 0),
                    loading_new,
                    False,
                )
            total_msg += len(self.channels[channel.id].messages)
            total_chan += 1
        yield total_msg, total_chan, loading_new, True
        # write logs
        with open(self.log_file, mode="w") as f:
            f.write(json.dump(self.dict()))
