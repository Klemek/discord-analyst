from typing import List, Optional
from collections import defaultdict


from utils import mention, channel_mention, plural, percent, top_key, val_sum


class Presence:
    def __init__(self):
        self.messages = defaultdict(int)
        self.reactions = defaultdict(int)
        self.used_reaction = defaultdict(int)
        self.channel_usage = defaultdict(int)
        self.channel_total = defaultdict(int)
        self.mentions = defaultdict(int)
        self.mention_others = defaultdict(int)
        self.mention_count = defaultdict(int)

    def to_string(
        self,
        msg_count: int,
        total_msg: int,
        *,
        chan_count: Optional[int],
        show_top_channel: bool,
        member_specific: bool,
    ) -> List[str]:
        ret = []
        if chan_count is None:
            type = "server's"
        elif chan_count == 1:
            type = "channel's"
        else:
            type = "channels'"
        if member_specific:
            ret += [
                f"- **messages**: {msg_count:,} ({percent(msg_count/total_msg)} of {type})"
            ]
        else:
            top_member = top_key(self.messages)
            ret += [
                f"- **top messages**:  {mention(top_member)} ({self.messages[top_member]} msg, {percent(self.messages[top_member]/val_sum(self.messages))})"
            ]
        if show_top_channel:
            top_channel = top_key(self.channel_usage)
            channel_sum = val_sum(self.channel_usage)
            found_in = sorted(
                self.channel_usage,
                key=lambda k: self.channel_usage[k] / self.channel_total[k],
            )[-1]
            ret += [
                f"- **most visited channel**: {channel_mention(top_channel)} ({self.channel_usage[top_channel]:,} msg, {percent(self.channel_usage[top_channel]/channel_sum)})",
            ]
            if member_specific:
                ret += [
                    f"- **most contributed channel**: {channel_mention(found_in)} ({self.channel_usage[found_in]:,} msg, {percent(self.channel_usage[found_in]/self.channel_total[found_in])} of {type})"
                ]
        if member_specific:
            if len(self.mentions) > 0:
                top_mention = top_key(self.mentions)
                mention_sum = val_sum(self.mentions)
                ret += [
                    f"- **was mentioned**: {plural(mention_sum, 'time')} ({percent(mention_sum/val_sum(self.mention_count))} of {type})",
                    f"- **mostly mentioned by**: {mention(top_mention)} ({plural(self.mentions[top_mention], 'time')}, {percent(self.mentions[top_mention]/mention_sum)})",
                ]
        if len(self.mention_others) > 0:
            top_mention = top_key(self.mention_others)
            mention_sum = val_sum(self.mention_others)
            if member_specific:
                ret += [
                    f"- **mentioned others**: {plural(mention_sum, 'time')} ({percent(mention_sum/val_sum(self.mention_count))} of {type})",
                    f"- **mostly mentioned**: {mention(top_mention)} ({plural(self.mention_others[top_mention], 'time')}, {percent(self.mention_others[top_mention]/mention_sum)})",
                ]
            else:
                top_member = top_key(self.mention_count)
                ret += [
                    f"- **mentioned**: {plural(mention_sum, 'time')} ({mention(top_member)}, {percent(self.mention_count[top_member]/val_sum(self.mention_count))})",
                    f"- **top mentions**: {mention(top_member)} ({plural(self.mention_count[top_member], 'time')}, {percent(self.mention_count[top_member]/val_sum(self.mention_count))})",
                    f"- **most mentioned**: {mention(top_mention)} ({plural(self.mention_others[top_mention], 'time')}, {percent(self.mention_others[top_mention]/mention_sum)})",
                ]
        if len(self.reactions) > 0:
            total_used = val_sum(self.reactions)
            top_reaction = top_key(self.reactions)
            ret += [
                f"- **reactions**: {plural(total_used, 'time')}",
                f"- **most used reaction**: {top_reaction} ({plural(self.reactions[top_reaction], 'time')}, {percent(self.reactions[top_reaction]/total_used)})",
            ]
            if member_specific:
                ret[
                    -2
                ] += f" ({percent(total_used/val_sum(self.used_reaction))} of {type})"
            else:
                top_member = top_key(self.used_reaction)
                ret.insert(
                    -1,
                    f"- **top reactions**: {mention(top_member)} ({plural(self.used_reaction[top_member], 'time')}, {percent(self.used_reaction[top_member]/val_sum(self.used_reaction))})",
                )
        return ret
