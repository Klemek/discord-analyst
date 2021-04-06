from typing import List
import random

# Custom libs

from utils import mention, from_now, str_datetime, message_link


class History:
    def __init__(self):
        self.messages = []

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
