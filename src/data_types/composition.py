from typing import List
from collections import defaultdict

from utils import percent, top_key, plural, precise, val_sum


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
        total_emotes = val_sum(self.emotes)
        top_emote = top_key(self.emotes)
        ret = [
            f"- **avg. characters / message**: {self.total_characters/msg_count:.2f}",
            f"- **plain text messages**: {self.plain_text:,} ({percent(self.plain_text/msg_count)})"
            if self.plain_text > 0
            else "",
            f"- **edited messages**: {self.edited:,} ({percent(self.edited/msg_count)})"
            if self.edited > 0
            else "",
            f"- **@\u200beveryone**: {self.everyone:,} ({percent(self.everyone/msg_count)})"
            if self.everyone > 0
            else "",
            f"- **mentions**: {self.mentions:,} (in {percent(self.mention_msg/msg_count)} of msg, avg. {precise(self.mentions/msg_count)}/msg)"
            if self.mentions > 0
            else "",
            f"- **answers**: {self.answers:,} ({percent(self.answers/msg_count)})"
            if self.answers > 0
            else "",
            f"- **emojis**: {total_emotes:,} (in {percent(self.emote_msg/msg_count)} of msg, avg. {precise(total_emotes/msg_count)}/msg)"
            if total_emotes > 0
            else "",
            f"- **most used emoji**: {top_emote} ({plural(self.emotes[top_emote], 'time')}, {percent(self.emotes[top_emote]/total_emotes)})"
            if total_emotes > 0
            else "",
            f"- **emoji-only messages**: {self.emote_only:,} ({percent(self.emote_only/msg_count)})"
            if self.emote_only > 0
            else "",
            f"- **images**: {self.images:,} ({percent(self.images/msg_count)})"
            if self.images > 0
            else "",
            f"- **links**: {self.links:,} ({percent(self.link_msg/msg_count)})"
            if self.links > 0
            else "",
            f"- **spoilers**: {self.spoilers:,} ({percent(self.spoilers/msg_count)})"
            if self.spoilers > 0
            else "",
            f"- **tts messages**: {self.tts:,} ({percent(self.tts/msg_count)})"
            if self.tts > 0
            else "",
        ]
        return ret
