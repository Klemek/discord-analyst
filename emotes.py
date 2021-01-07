from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import discord


# Custom libs

from utils import no_duplicate, mention, plural, day_interval, get_intro
from log_manager import GuildLogs, ChannelLogs
import emojis

# CONSTANTS

CHUNK_SIZE = 1000

# MAIN

HELP = (
    "```\n"
    + "%emotes : Rank emotes by their usage\n"
    + "arguments:\n"
    + "* @member : filter for one or more member\n"
    + "* #channel : filter for one or more channel\n"
    + "* <n> : top <n> emojis, default is 20\n"
    + "* all : list all common emojis in addition to this guild's\n"
    + "* members : show top member for each emote\n"
    + "Example: %emotes 10 all #mychannel1 #mychannel2 @user\n"
    + "```"
)


async def compute(client: discord.client, message: discord.Message, *args: str):
    """
    Computes the %emotes command
    """
    guild = message.guild
    logs = GuildLogs(guild)

    # If "%emotes help" redirect to "%help emotes"
    if "help" in args:
        await client.bot.help(client, message, "help", "emotes")
        return

    # check args validity
    str_channel_mentions = [channel.mention for channel in message.channel_mentions]
    str_mentions = [member.mention for member in message.mentions]
    for arg in args[1:]:
        if (
            arg not in ["all", "members"]
            and not arg.isdigit()
            and arg not in str_channel_mentions
            and arg not in str_mentions
        ):
            await message.channel.send(f"Unrecognized argument: `{arg}`")
            return

    # Create emotes dict from custom emojis of the guild
    emotes = defaultdict(Emote)
    for emoji in guild.emojis:
        emotes[str(emoji)] = Emote(emoji)

    # Get selected channels or all of them if no channel arguments
    channels = no_duplicate(message.channel_mentions)
    full = len(channels) == 0
    if full:
        channels = guild.text_channels

    # Get selected members
    members = no_duplicate(message.mentions)
    raw_members = no_duplicate(message.raw_mentions)

    # get max emotes to view
    top = 20
    for arg in args:
        if arg.isdigit():
            top = int(arg)

    # check other args
    all_emojis = "all" in args
    show_members = "members" in args and (len(members) == 0 or len(members) > 1)

    # Start computing data
    async with message.channel.typing():
        progress = await message.channel.send("```Starting analysis...```")
        total_msg, total_chan = await logs.load(progress, channels)
        if total_msg == -1:
            await message.channel.send(
                f"{message.author.mention} An analysis is already running on this server, please be patient."
            )
        else:
            msg_count = 0
            chan_count = 0
            for id in logs.channels:
                count = analyse_channel(
                    logs.channels[id], emotes, raw_members, all_emojis=all_emojis
                )
                msg_count += count
                chan_count += 1 if count > 0 else 0
            await progress.edit(content="```Computing results...```")
            # Display results
            await tell_results(
                get_intro(
                    "emotes usage",
                    emotes,
                    full,
                    channels,
                    members,
                    msg_count,
                    chan_count,
                ),
                emotes,
                message.channel,
                total_msg,
                top=top,
                allow_unused=full and len(members) == 0,
                show_life=False,
                show_members=show_members,
            )
        # Delete custom progress message
        await progress.delete()


# CLASSES


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


# ANALYSIS


def analyse_channel(
    channel: ChannelLogs,
    emotes: Dict[str, Emote],
    raw_members: List[int],
    *,
    all_emojis: bool,
) -> int:
    count = 0
    for message in channel.messages:
        # If author is included in the selection (empty list is all)
        if not message.bot and (len(raw_members) == 0 or message.author in raw_members):
            count += 1
            # Find all emotes un the current message in the form "<:emoji:123456789>"
            # Filter for known emotes
            found = emojis.regex.findall(message.content)
            # For each emote, update its usage
            for name in found:
                if name not in emotes:
                    if not all_emojis or name not in emojis.unicode_list:
                        continue
                emotes[name].usages += 1
                emotes[name].update_use(message.created_at, [message.author])
        # For each reaction of this message, test if known emote and update when it's the case
        for name in message.reactions:
            if name not in emotes:
                if not all_emojis or name not in emojis.unicode_list:
                    continue
            if len(raw_members) == 0:
                emotes[name].reactions += len(message.reactions[name])
                emotes[name].update_use(message.created_at, message.reactions[name])
            else:
                for member in raw_members:
                    if member in message.reactions[name]:
                        emotes[name].reactions += 1
                        emotes[name].update_use(message.created_at, [member])
    return count


# RESULTS


async def tell_results(
    intro: str,  # introduction sentence (from get_intro)
    emotes: Dict[str, Emote],
    channel: discord.TextChannel,
    nmm: int,  # number of impacted messages
    top: int,  # top n emojis
    *,
    allow_unused: bool,
    show_life: bool,
    show_members: bool,
):
    names = [name for name in emotes]
    names.sort(key=lambda name: emotes[name].score(), reverse=True)
    names = names[:top]
    res = [intro]
    res += [
        emotes[name].to_string(names.index(name), name, show_life, show_members)
        for name in names
        if allow_unused or emotes[name].used()
    ]
    res += [get_total(emotes, nmm)]
    response = ""
    for r in res:
        if len(response + "\n" + r) > 2000:
            await channel.send(response)
            response = ""
        response += "\n" + r
    if len(response) > 0:
        await channel.send(response)


def get_total(emotes: Dict[str, Emote], nmm: int) -> str:
    """
    Get the total of all emotes used
    """
    nu = 0
    nr = 0
    for name in emotes:
        nu += emotes[name].usages
        nr += emotes[name].reactions
    if nr > 0:
        return f"Total: {nu:,} times ({nu / nmm:.4f} / message) and {nr:,} reactions"
    else:
        return f"Total: {nu:,} times ({nu / nmm:.4f} / message)"
