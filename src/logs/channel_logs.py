from typing import Union, Tuple
import discord

from . import MessageLog
from utils import FakeMessage

CHUNK_SIZE = 2000
FORMAT = 3


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
            if not self.is_format():
                return
            self.id = int(channel["id"])
            self.name = channel["name"]
            self.last_message_id = (
                int(channel["last_message_id"])
                if channel["last_message_id"] is not None
                else None
            )
            self.messages = [MessageLog(message) for message in channel["messages"]]

    def is_format(self):
        return self.format == FORMAT

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
                sanity_check = len(await channel.history(limit=1).flatten())
                if sanity_check == 1:
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
            yield -1, True
            return  # When an exception occurs (like Forbidden)
        yield len(self.messages), True

    def dict(self) -> dict:
        channel = dict(self.__dict__)
        channel.pop("channel", None)
        channel["messages"] = [message.dict() for message in self.messages]
        return channel
