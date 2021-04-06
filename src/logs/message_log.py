from typing import Union, Any
import discord
from datetime import datetime

from utils import is_extension

IMAGE_FORMAT = [".gif", ".gifv", ".png", ".jpg", ".jpeg", ".bmp"]
EMBED_IMAGES = ["image", "gifv"]


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
            for attachment in message.attachments:
                if is_extension(attachment.filename, IMAGE_FORMAT):
                    self.image = True
                    break
            else:
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
            self.embed = message["embed"]
            self.attachment = message["attachment"]
            self.reactions = message["reactions"]

    async def load(self, message: discord.Message):
        for reaction in message.reactions:
            self.reactions[str(reaction.emoji)] = []
            async for user in reaction.users():
                self.reactions[str(reaction.emoji)] += [user.id]

    def dict(self) -> dict:
        message = dict(self.__dict__)
        message.pop("channel", None)
        message["created_at"] = self.created_at.isoformat()
        message["edited_at"] = (
            self.edited_at.isoformat() if self.edited_at is not None else None
        )
        return message
