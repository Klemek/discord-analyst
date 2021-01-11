from typing import List
from collections import defaultdict


from utils import mention, channel_mention, plural


class Presence:
    def __init__(self):
        self.most_used_reaction = ""
        self.most_used_reaction_count = 0
        self.used_reaction_total = 1
        self.channel_usage = defaultdict(int)
        self.mentions = defaultdict(int)

    def to_string(self, *, show_top_channel: bool, show_mentioned: bool) -> List[str]:
        ret = []
        if show_top_channel:
            top_channel = sorted(self.channel_usage)[-1]
            channel_sum = sum(self.channel_usage.values())
            ret += [
                f"- **most visited channel**: {channel_mention(top_channel)} ({self.channel_usage[top_channel]:,} msg, {100*self.channel_usage[top_channel]//channel_sum:.0f}%)"
            ]
        if show_mentioned:
            if len(self.mentions) > 0:
                top_mention = sorted(self.mentions)[-1]
                mention_sum = sum(self.mentions.values())
                ret += [
                    f"- **mentioned**: {plural(mention_sum, 'time')}",
                    f"- **mostly mentioned by**: {mention(top_mention)} ({plural(self.mentions[top_mention], 'time')}, {100*self.mentions[top_mention]//mention_sum:.0f}%)",
                ]
            else:
                ret += [f"- **mentioned**: 0 times"]
        if self.used_reaction_total > 0:
            ret += [
                f"- **reactions**: {plural(self.used_reaction_total, 'time')}",
                f"- **most used reaction**: {self.most_used_reaction} ({plural(self.most_used_reaction_count, 'time')}, {100*self.most_used_reaction_count/self.used_reaction_total:.0f}%)",
            ]
        else:
            ret += [f"- **reactions**: 0 times"]
        return ret
