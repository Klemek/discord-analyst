from typing import List
from collections import defaultdict


from utils import mention, channel_mention, plural, percent, top_key


class Presence:
    def __init__(self):
        self.reactions = defaultdict(int)
        self.used_reaction_total = 0
        self.channel_usage = defaultdict(int)
        self.channel_total = defaultdict(int)
        self.mentions = defaultdict(int)
        self.mention_others = defaultdict(int)
        self.mention_count = 0

    def to_string(
        self,
        msg_count: int,
        total_msg: int,
        *,
        show_top_channel: bool,
        member_specific: bool,
    ) -> List[str]:
        ret = []
        if member_specific:
            ret += [
                f"- **messages**: {msg_count} ({percent(msg_count/total_msg)} of server's)"
            ]
        if show_top_channel:
            top_channel = top_key(self.channel_usage)
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
                top_mention = top_key(self.mentions)
                mention_sum = sum(self.mentions.values())
                ret += [
                    f"- **was mentioned**: {plural(mention_sum, 'time')} ({percent(mention_sum/self.mention_count)} of server's)",
                    f"- **mostly mentioned by**: {mention(top_mention)} ({plural(self.mentions[top_mention], 'time')}, {percent(self.mentions[top_mention]/mention_sum)})",
                ]
            else:
                ret += ["- **was mentioned**: 0 times"]
            if len(self.mention_others) > 0:
                top_mention = top_key(self.mention_others)
                mention_sum = sum(self.mention_others.values())
                ret += [
                    f"- **mentioned others**: {plural(mention_sum, 'time')} ({percent(mention_sum/self.mention_count)} of server's)",
                    f"- **mostly mentioned**: {mention(top_mention)} ({plural(self.mention_others[top_mention], 'time')}, {percent(self.mention_others[top_mention]/mention_sum)})",
                ]
            else:
                ret += ["- **was mentioned**: 0 times"]

        if len(self.reactions) > 0:
            total_used = sum(self.reactions.values())
            top_reaction = top_key(self.reactions)
            ret += [
                f"- **reactions**: {plural(total_used, 'time')}",
                f"- **most used reaction**: {top_reaction} ({plural(self.reactions[top_reaction], 'time')}, {percent(self.reactions[top_reaction]/total_used)})",
            ]
            if member_specific:
                ret[
                    -2
                ] += f" ({percent(total_used/self.used_reaction_total)} of server's)"
        else:
            ret += ["- **reactions**: 0 times"]
        return ret
