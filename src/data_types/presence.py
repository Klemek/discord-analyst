from typing import List
from collections import defaultdict


from utils import mention, channel_mention, plural, percent


class Presence:
    def __init__(self):
        self.most_used_reaction = ""
        self.most_used_reaction_count = 0
        self.used_reaction_total = 1
        self.used_reaction_all_total = 1
        self.channel_usage = defaultdict(int)
        self.channel_total = defaultdict(int)
        self.mentions = defaultdict(int)
        self.mention_others = defaultdict(int)
        self.msg_count = 0
        self.total_msg = 0
        self.mention_count = 0

    def to_string(self, *, show_top_channel: bool, member_specific: bool) -> List[str]:
        ret = []
        if member_specific:
            ret += [
                f"- **messages**: {self.msg_count} ({percent(self.msg_count/self.total_msg)} of server's)"
            ]
        if show_top_channel:
            top_channel = sorted(self.channel_usage)[-1]
            channel_sum = sum(self.channel_usage.values())
            found_in = sorted(
                self.channel_usage,
                key=lambda k: self.channel_usage[k] / self.channel_total[k],
            )[-1]
            ret += [
                f"- **most visited channel**: {channel_mention(top_channel)} ({self.channel_usage[top_channel]:,} msg, {percent(self.channel_usage[top_channel]/channel_sum)})",
                f"- **mostly found in**: {channel_mention(found_in)} ({self.channel_usage[found_in]:,} msg, {percent(self.channel_usage[found_in]/self.channel_total[found_in])} of channel's)",
            ]
        if member_specific:
            if len(self.mentions) > 0:
                top_mention = sorted(self.mentions)[-1]
                mention_sum = sum(self.mentions.values())
                ret += [
                    f"- **was mentioned**: {plural(mention_sum, 'time')} ({percent(mention_sum/self.mention_count)} of server's)",
                    f"- **mostly mentioned by**: {mention(top_mention)} ({plural(self.mentions[top_mention], 'time')}, {percent(self.mentions[top_mention]/mention_sum)})",
                ]
            else:
                ret += ["- **was mentioned**: 0 times"]
            if len(self.mention_others) > 0:
                top_mention = sorted(self.mention_others)[-1]
                mention_sum = sum(self.mention_others.values())
                ret += [
                    f"- **mentioned others**: {plural(mention_sum, 'time')} ({percent(mention_sum/self.mention_count)} of server's)",
                    f"- **mostly mentioned**: {mention(top_mention)} ({plural(self.mention_others[top_mention], 'time')}, {percent(self.mention_others[top_mention]/mention_sum)})",
                ]
            else:
                ret += ["- **was mentioned**: 0 times"]
        if self.used_reaction_total > 0:
            # ({self.used_reaction_total/self.used_reaction_all_total})
            ret += [
                f"- **reactions**: {plural(self.used_reaction_total, 'time')}",
                f"- **most used reaction**: {self.most_used_reaction} ({plural(self.most_used_reaction_count, 'time')}, {percent(self.most_used_reaction_count/self.used_reaction_total)})",
            ]
            if member_specific:
                ret[
                    -2
                ] += f" ({percent(self.used_reaction_total/self.used_reaction_all_total)} of server's)"
        else:
            ret += ["- **reactions**: 0 times"]
        return ret
