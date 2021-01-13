from typing import List
from collections import defaultdict

from utils import percent, top_key, plural, precise


class Composition:
    def __init__(self):
        self.total_characters = 0
        self.plain_text = 0
        self.emote_msg = 0
        self.emote_only = 0
        self.emotes = defaultdict(int)
        self.edited = 0
        self.everyone = 0
        self.answers = 0
        self.images = 0
        self.tts = 0
        self.mentions = 0
        self.mention_msg = 0
        self.links = 0
        self.link_msg = 0
        self.spoilers = 0

    def to_string(self, msg_count: int) -> List[str]:
        ret = []
        ret += [
            f"- **avg. characters / message**: {self.total_characters/msg_count:.2f}"
        ]
        if self.plain_text > 0:
            ret += [
                f"- **plain text messages**: {self.plain_text:,} ({percent(self.plain_text/msg_count)})"
            ]
        if self.edited > 0:
            ret += [
                f"- **edited messages**: {self.edited:,} ({percent(self.edited/msg_count)})"
            ]
        if self.everyone > 0:
            ret += [
                f"- **@\u200beveryone**: {self.everyone:,} ({percent(self.everyone/msg_count)})"
            ]
        if self.mentions > 0:
            ret += [
                f"- **mentions**: {self.mentions:,} (in {percent(self.mention_msg/msg_count)} of msg, avg. {precise(self.mentions/msg_count)}/msg)",
            ]
        if self.answers > 0:
            ret += [
                f"- **answers**: {self.answers:,} ({percent(self.answers/msg_count)})"
            ]
        total_emotes = sum(self.emotes.values())
        if total_emotes > 0:
            top_emote = top_key(self.emotes)
            ret += [
                f"- **emojis**: {total_emotes:,} (in {percent(self.emote_msg/msg_count)} of msg, avg. {precise(total_emotes/msg_count)}/msg)",
                f"- **most used emoji**: {top_emote} ({plural(self.emotes[top_emote], 'time')}, {percent(self.emotes[top_emote]/total_emotes)})",
            ]
            if self.emote_only > 0:
                ret += [
                    f"- **emoji-only messages**: {self.emote_only:,} ({percent(self.emote_only/msg_count)})"
                ]
        if self.images > 0:
            ret += [f"- **images**: {self.images:,} ({percent(self.images/msg_count)})"]
        if self.links > 0:
            ret += [f"- **links**: {self.links:,} ({percent(self.link_msg/msg_count)})"]
        if self.spoilers > 0:
            ret += [
                f"- **spoilers**: {self.spoilers:,} ({percent(self.spoilers/msg_count)})"
            ]
        if self.tts > 0:
            ret += [f"- **tts messages**: {self.tts:,} ({percent(self.tts/msg_count)})"]
        return ret
