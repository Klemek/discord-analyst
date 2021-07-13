import logging
from typing import Union, Tuple, Any
import discord
from datetime import datetime

from . import MessageLog
from utils import serialize, FakeMessage

CHUNK_SIZE = 2000
FORMAT = 3


class ChannelLogs:
    def __init__(self, channel: Union[discord.TextChannel, dict], guild: Any):
        self.guild = guild
        if isinstance(channel, discord.TextChannel):
            self.id = channel.id
            self.name = channel.name
            self.last_message_id = None
            self.first_message_id = None
            self.format = FORMAT
            self.messages = set()
            self.start_date = None
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
            self.first_message_id = (
                int(channel["first_message_id"])
                if "first_message_id" in channel
                and channel["first_message_id"] is not None
                else None
            )
            self.messages = {
                MessageLog(message, self) for message in channel["messages"]
            }
            self.start_date = (
                self.sorted_messages[0].created_at if len(self.messages) > 0 else None
            )

    def is_format(self):
        return self.format == FORMAT

    def preload(self, channel: discord.TextChannel):
        self.name = channel.name
        self.channel = channel

    @property
    def sorted_messages(self):
        return sorted(self.messages)

    @property
    def nsfw(self):
        self.channel.nsfw

    async def load(
        self, channel: discord.TextChannel, start_date: datetime, stop_date: datetime
    ) -> Tuple[int, int]:
        is_empty = self.last_message_id is None
        try:
            if is_empty:
                sanity_check = len(await channel.history(limit=1).flatten())
                if sanity_check != 1:
                    yield len(self.messages), True
                    return
            # load backward
            if is_empty or (
                self.first_message_id is not None
                and (
                    start_date is None
                    or (self.start_date is not None and self.start_date > start_date)
                )
            ):
                first_message_date = None
                tmp_message_id = 0
                done = 0
                while (
                    first_message_date is None
                    or (
                        done >= CHUNK_SIZE
                        and (start_date is None or first_message_date > start_date)
                    )
                ) and tmp_message_id != self.first_message_id:
                    tmp_message_id = self.first_message_id
                    done = 0
                    async for message in channel.history(
                        limit=CHUNK_SIZE,
                        before=FakeMessage(self.first_message_id)
                        if self.first_message_id is not None
                        else None,
                        oldest_first=False,
                    ):
                        done += 1
                        self.first_message_id = message.id
                        first_message_date = message.created_at
                        m = MessageLog(message, self)
                        await m.load(message)
                        self.messages.add(m)
                    yield len(self.messages), False
                if done < CHUNK_SIZE:  # reached bottom
                    self.first_message_id = None
                self.last_message_id = channel.last_message_id
            # load forward
            last_message_date = self.sorted_messages[-1].created_at
            if not is_empty and (stop_date is None or last_message_date < stop_date):
                tmp_message_id = None
                while (
                    self.last_message_id != channel.last_message_id
                    and (stop_date is None or last_message_date < stop_date)
                ) and self.last_message_id != tmp_message_id:
                    tmp_message_id = self.last_message_id
                    async for message in channel.history(
                        limit=CHUNK_SIZE,
                        after=FakeMessage(self.first_message_id),
                        oldest_first=True,
                    ):
                        last_message_date = message.created_at
                        self.last_message_id = message.id
                        m = MessageLog(message, self)
                        await m.load(message)
                        self.messages.add(m)
                    yield len(self.messages), False
        except discord.errors.HTTPException as e:
            yield -1, True
            return  # When an exception occurs (like Forbidden)
        self.start_date = (
            self.sorted_messages[0].created_at if len(self.messages) > 0 else None
        )
        yield len(self.messages), True

    def dict(self) -> dict:
        channel = serialize(self, not_serialized=["channel", "guild", "start_date"])
        channel["messages"] = [message.dict() for message in self.messages]
        return channel
