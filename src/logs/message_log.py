from typing import Optional, Union, Any
import discord
from datetime import datetime

from utils import (
    serialize,
    has_image,
)


class MessageLog:
    def __init__(self, message: Union[discord.Message, dict], channel: Any):
        self.channel = channel
        if isinstance(message, discord.Message):
            self.id = message.id
            self.created_at = message.created_at
            self.edited_at = message.edited_at
            self.author = message.author.id
            self.pinned = message.pinned
            self.mention_everyone = message.mention_everyone
            self.tts = message.tts
            self.bot = message.author.bot or message.author.system
            self.content = message.content
            self.mentions = message.raw_mentions
            if message.reference is not None:
                self.reference = message.reference.message_id
                if message.reference.resolved is not None:
                    try:
                        self.mentions += [message.reference.resolved.author.id]
                    except AttributeError:
                        pass
            else:
                self.reference = None
            self.role_mentions = message.raw_role_mentions
            self.channel_mentions = message.raw_channel_mentions
            self.image = False
            self.attachment = len(message.attachments) > 0
            self.embed = len(message.embeds) > 0
            self.image = has_image(message)
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
            self.embed = message["embed"]
            self.attachment = message["attachment"]
            self.reactions = message["reactions"]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __gt__(self, other: "MessageLog") -> bool:
        return self.created_at > other.created_at

    def __hash__(self) -> int:
        return self.id

    async def load(self, message: discord.Message):
        for reaction in message.reactions:
            self.reactions[str(reaction.emoji)] = []
            async for user in reaction.users():
                self.reactions[str(reaction.emoji)] += [user.id]

    async def fetch(self) -> Optional[discord.Message]:
        try:
            return await self.channel.channel.fetch_message(self.id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    def dict(self) -> dict:
        return serialize(
            self, not_serialized=["channel"], dates=["created_at", "edited_at"]
        )
