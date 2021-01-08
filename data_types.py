from typing import List, Optional
from datetime import datetime
from collections import defaultdict
import discord

# Custom libs

from utils import mention, plural, day_interval


class Emote:
    """
    Custom class to store emotes data
    """

    def __init__(self, emoji: Optional[discord.Emoji] = None):
        self.emoji = emoji
        self.usages = 0
        self.reactions = 0
        self.last_used = None
        self.members = defaultdict(int)

    def update_use(self, date: datetime, members_id: List[int]):
        """
        Update last use date if more recent and last member
        """
        if self.last_used is None or date > self.last_used:
            self.last_used = date
        for member_id in members_id:
            self.members[member_id] += 1

    def used(self) -> bool:
        return self.usages > 0 or self.reactions > 0

    def score(self) -> float:
        # Score is compose of usages + reactions
        # When 2 emotes have the same score,
        # the days since last use is stored in the digits
        # (more recent first)
        return self.usages + self.reactions + 1 / (100000 * (self.use_days() + 1))

    def life_days(self) -> int:
        return (datetime.today() - self.emoji.created_at).days

    def use_days(self) -> int:
        # If never used, use creation date instead
        if self.last_used is None:
            return self.life_days()
        else:
            return (datetime.today() - self.last_used).days

    def get_top_member(self) -> int:
        return sorted(self.members.keys(), key=lambda id: self.members[id])[-1]

    def to_string(self, i: int, name: str, show_life: bool, show_members: bool) -> str:
        # place
        output = ""
        if i == 0:
            output += ":first_place:"
        elif i == 1:
            output += ":second_place:"
        elif i == 2:
            output += ":third_place:"
        else:
            output += f"**#{i + 1}**"
        output += f" {name} - "
        if not self.used():
            output += "never used "
        else:
            output += f"{plural(self.usages, 'time')} "
        if self.reactions >= 1:
            output += f"and {plural(self.usages, 'reaction')} "
        if show_life and not self.default:
            output += f"(in {plural(self.life_days(), 'day')}) "
        if self.used():
            output += f"(last used {day_interval(self.use_days())})"
            if show_members:
                output += f" (mostly by {mention(self.get_top_member())}: {self.members[self.get_top_member()]})"
        return output
