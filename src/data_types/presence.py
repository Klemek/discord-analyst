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
        if chan_count is None:
            type = "server's"
        elif chan_count == 1:
            type = "channel's"
        else:
            type = "channels'"
        top_member = top_key(self.messages)
        top_channel = top_key(self.channel_usage)
        channel_sum = val_sum(self.channel_usage)
        found_in = top_key(
            self.channel_usage,
            key=lambda k: self.channel_usage[k] / self.channel_total[k],
        )
        top_mention = top_key(self.mentions)
        mention_sum = val_sum(self.mentions)
        top_mention_others = top_key(self.mention_others)
        mention_others_sum = val_sum(self.mention_others)
        top_member_mentioned = top_key(self.mention_count)
        total_reaction_used = val_sum(self.reactions)
        top_reaction = top_key(self.reactions)
        top_reaction_member = top_key(self.used_reaction)

        ret = [
            f"- **messages**: {msg_count:,} ({percent(msg_count/total_msg)} of {type})"
            if member_specific
            else f"- **top messages**:  {mention(top_member)} ({self.messages[top_member]:,} msg, {percent(self.messages[top_member]/val_sum(self.messages))})",
            f"- **most visited channel**: {channel_mention(top_channel)} ({self.channel_usage[top_channel]:,} msg, {percent(self.channel_usage[top_channel]/channel_sum)})"
            if show_top_channel
            else "",
            f"- **most contributed channel**: {channel_mention(found_in)} ({self.channel_usage[found_in]:,} msg, {percent(self.channel_usage[found_in]/self.channel_total[found_in])} of {type})"
            if show_top_channel and member_specific
            else "",
            f"- **was mentioned**: {plural(mention_sum, 'time')} ({percent(mention_sum/val_sum(self.mention_count))} of {type})"
            if member_specific and len(self.mentions) > 0
            else "",
            f"- **mostly mentioned by**: {mention(top_mention)} ({plural(self.mentions[top_mention], 'time')}, {percent(self.mentions[top_mention]/mention_sum)})"
            if member_specific and len(self.mentions) > 0
            else "",
            f"- **mentioned others**: {plural(mention_others_sum, 'time')} ({percent(mention_others_sum/val_sum(self.mention_count))} of {type})"
            if len(self.mention_others) > 0 and member_specific
            else "",
            f"- **mostly mentioned**: {mention(top_mention_others)} ({plural(self.mention_others[top_mention_others], 'time')}, {percent(self.mention_others[top_mention_others]/mention_others_sum)})"
            if len(self.mention_others) > 0 and member_specific
            else "",
            f"- **mentioned**: {plural(mention_others_sum, 'time')} ({mention(top_member_mentioned)}, {percent(self.mention_count[top_member_mentioned]/val_sum(self.mention_count))})"
            if len(self.mention_others) > 0 and not member_specific
            else "",
            f"- **top mentions**: {mention(top_member_mentioned)} ({plural(self.mention_count[top_member_mentioned], 'time')}, {percent(self.mention_count[top_member_mentioned]/val_sum(self.mention_count))})"
            if len(self.mention_others) > 0 and not member_specific
            else "",
            f"- **most mentioned**: {mention(top_mention_others)} ({plural(self.mention_others[top_mention_others], 'time')}, {percent(self.mention_others[top_mention_others]/mention_others_sum)})"
            if len(self.mention_others) > 0 and not member_specific
            else "",
            f"- **reactions**: {plural(total_reaction_used, 'time')}"
            if len(self.reactions) > 0 and not member_specific
            else "",
            f"- **reactions**: {plural(total_reaction_used, 'time')} ({percent(total_reaction_used/val_sum(self.used_reaction))} of {type})"
            if len(self.reactions) > 0 and member_specific
            else "",
            f"- **top reactions**: {mention(top_reaction_member)} ({plural(self.used_reaction[top_reaction_member], 'time')}, {percent(self.used_reaction[top_reaction_member]/val_sum(self.used_reaction))})"
            if len(self.reactions) > 0 and not member_specific
            else "",
            f"- **most used reaction**: {top_reaction} ({plural(self.reactions[top_reaction], 'time')}, {percent(self.reactions[top_reaction]/total_reaction_used)})"
            if len(self.reactions) > 0
            else "",
        ]
        return ret
