from typing import List, Optional, Dict
from datetime import datetime
from collections import defaultdict
import discord

# Custom libs

from utils import mention, plural, from_now, top_key, percent


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

    def score(self, *, usage_weight: int = 1, react_weight: int = 1) -> float:
        # Score is compose of usages + reactions
        # When 2 emotes have the same score,
        # the days since last use is stored in the digits
        # (more recent first)
        return (
            self.usages * usage_weight
            + self.reactions * react_weight
            + 1 / (100000 * (self.use_days() + 1))
        )

    def life_days(self) -> int:
        return (datetime.today() - self.emoji.created_at).days

    def use_days(self) -> int:
        # If never used, use creation date instead
        if self.last_used is None:
            return self.life_days()
        else:
            return (datetime.today() - self.last_used).days

    def get_top_member(self) -> int:
        return top_key(self.members)

    def to_string(
        self,
        i: int,
        name: str,
        *,
        total_usage: int,
        total_react: int,
        show_life: bool,
        show_members: bool,
    ) -> str:
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
            output += "never used"
        else:
            if self.usages > 0:
                output += f"{plural(self.usages, 'time')} ({percent(self.usages/total_usage)})"
            if self.usages > 0 and self.reactions > 0:
                output += " and "
            if self.reactions >= 1:
                output += f"{plural(self.reactions, 'reaction')} ({percent(self.reactions/total_react)})"
            output += f" (last used {from_now(self.last_used)})"
            if show_members:
                top_member = self.get_top_member()
                total = self.usages + self.reactions
                if total == self.members[top_member]:
                    output += f" (all by {mention(top_member)})"
                else:
                    output += f" ({self.members[top_member]} by {mention(top_member)}, {percent(self.members[top_member]/total)})"
        if show_life and not self.default:
            output += f" (in {plural(self.life_days(), 'day')})"
        return output


def get_emote_dict(guild: discord.Guild) -> Dict[str, Emote]:
    emotes = defaultdict(Emote)
    for emoji in guild.emojis:
        emotes[str(emoji)] = Emote(emoji)
    return emotes
