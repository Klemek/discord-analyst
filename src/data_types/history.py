from typing import List
import random

# Custom libs

from utils import (
    mention,
    from_now,
    str_datetime,
    message_link,
    SPLIT_TOKEN,
    FilterLevel,
    should_allow_spoiler,
    is_image_gif,
)

MAX_RANDOM_TRIES = 100


class History:
    def __init__(self):
        self.messages = []

    async def to_string_image(
        self, *, type: str, spoiler: FilterLevel, gif_only: bool
    ) -> List[str]:
        if len(self.messages) == 0:
            return ["There was no messages matching your filters"]
        message = None
        intro = None
        real_message = None
        if type == "first":
            self.messages.sort(key=lambda m: m.created_at)
            index = 0
            while real_message is None and index < len(self.messages):
                message = self.messages[index]
                real_message = await message.fetch()
                if real_message is not None and (
                    not should_allow_spoiler(real_message, spoiler)
                    or (gif_only and not is_image_gif(real_message))
                ):
                    real_message = None
                index += 1
            intro = f"First image out of {len(self.messages):,}"
        elif type == "last":
            self.messages.sort(key=lambda m: m.created_at, reverse=True)
            index = 0
            while real_message is None and index < len(self.messages):
                message = self.messages[index]
                real_message = await message.fetch()
                if real_message is not None and (
                    not should_allow_spoiler(real_message, spoiler)
                    or (gif_only and not is_image_gif(real_message))
                ):
                    real_message = None
                index += 1
            intro = f"Last image out of {len(self.messages):,}"
        elif type == "random":
            intro = f"Random image out of {len(self.messages):,}"
            tries = 0
            while real_message is None and tries < MAX_RANDOM_TRIES:
                message = random.choice(self.messages)
                real_message = await message.fetch()
                if real_message is not None and (
                    not should_allow_spoiler(real_message, spoiler)
                    or (gif_only and not is_image_gif(real_message))
                ):
                    real_message = None
                tries += 1

        if real_message is None:
            return ["There was no messages matching your filters"]
        image = "<Error>"
        if len(real_message.attachments) > 0:
            image = real_message.attachments[0].url
        elif len(real_message.embeds) > 0:
            image = real_message.embeds[0].url

        return [
            intro,
            f"{str_datetime(message.created_at)} ({from_now(message.created_at)}) {mention(message.author)} sent:",
            f"<{message_link(message)}>",
            SPLIT_TOKEN,
            image,
        ]

    def to_string(self, *, type: str) -> List[str]:
        if len(self.messages) == 0:
            return ["There was no messages matching your filters"]
        message = None
        intro = None
        if type == "first":
            self.messages.sort(key=lambda m: m.created_at)
            message = self.messages[0]
            intro = f"First message out of {len(self.messages):,}"
        elif type == "last":
            self.messages.sort(key=lambda m: m.created_at, reverse=True)
            message = self.messages[0]
            intro = f"Last message out of {len(self.messages):,}"
        elif type == "random":
            message = random.choice(self.messages)
            intro = f"Random message out of {len(self.messages):,}"

        text = ["> " + line for line in message.content.splitlines()]
        if message.attachment:
            text += ["> <image>" if message.image else "> <attachment>"]

        return [
            intro,
            f"{str_datetime(message.created_at)} ({from_now(message.created_at)}) {mention(message.author)} said:",
            *text,
            f"<{message_link(message)}>",
        ]
