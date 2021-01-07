from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import discord
import re
import json
import logging

# Custom libs

from utils import aggregate, no_duplicate
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
    + "* reactions : add reaction analysis for members (long)\n"
    + "* all : list all common emojis in addition to this guild's\n"
    + "* <n> : top <n> emojis, default is 20\n"
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

    # Create emotes dict from custom emojis of the guild
    emotes = defaultdict(Emote)
    for emoji in guild.emojis:
        emotes[str(emoji)] = Emote(emoji)

    # Get selected channels or all of them if no channel arguments
    channels = no_duplicate(message.channel_mentions)
    full = len(channels) == 0
    if full:
        channels = guild.text_channels

    # get max emotes to view
    top = 20
    for arg in args:
        if arg.isdigit():
            top = int(arg)

    # Get selected members
    members = no_duplicate(message.mentions)
    raw_members = no_duplicate(message.raw_mentions)

    # Start computing data
    async with message.channel.typing():
        progress = await message.channel.send("```Starting analysis...```")
        total_msg, total_chan = await logs.load(progress, channels)
        if total_msg == -1:
            await message.channel.send(
                f"{message.author} An analysis is already running on this server, please be patient."
            )
        else:
            msg_count = 0
            chan_count = 0
            for id in logs.channels:
                count = analyse_channel(
                    logs.channels[id], emotes, raw_members, all_emojis="all" in args
                )
                msg_count += count
                chan_count += 1 if count > 0 else 0
            await progress.edit(content=f"```Computing results...```")
            # Display results
            await tell_results(
                get_intro(emotes, full, channels, members, msg_count, chan_count),
                emotes,
                message.channel,
                total_msg,
                top=top,
                allow_unused=full and len(members) == 0,
                show_life=False,
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

    def update_use(self, date: datetime):
        """
        Update last use date if more recent
        """
        if self.last_used is None or date > self.last_used:
            self.last_used = date

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
                emotes[name].update_use(message.created_at)
        # For each reaction of this message, test if known emote and update when it's the case
        for name in message.reactions:
            if name not in emotes:
                if not all_emojis or name not in emojis.unicode_list:
                    continue
            if len(raw_members) == 0:
                emotes[name].reactions += len(message.reactions[name])
                emotes[name].update_use(message.created_at)
            else:
                for member in raw_members:
                    if member in message.reactions[name]:
                        emotes[name].reactions += 1
                        emotes[name].update_use(message.created_at)
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
):
    names = [name for name in emotes]
    names.sort(key=lambda name: emotes[name].score(), reverse=True)
    names = names[:top]
    res = [intro]
    res += [
        f"{get_place(names.index(name))} {name} - "
        f"{get_usage(emotes[name])}"
        f"{get_reactions(emotes[name])}"
        f"{get_life(emotes[name], show_life)}"
        f"{get_last_used(emotes[name])}"
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


def get_intro(
    emotes: Dict[str, Emote],
    full: bool,
    channels: List[discord.TextChannel],
    members: List[discord.Member],
    nmm: int,  # number of messages impacted
    nc: int,  # number of impacted channels
) -> str:
    """
    Get the introduction sentence of the response
    """
    # Show all data (members, channels) when it's less than 5 units
    if len(members) == 0:
        # Full scan of the server
        if full:
            return f"{len(emotes)} emotes in this server ({nc} channels, {nmm:,} messages):"
        elif len(channels) < 5:
            return f"{aggregate([c.mention for c in channels])} emotes usage in {nmm:,} messages:"
        else:
            return f"These {len(channels)} channels emotes usage in {nmm:,} messages:"
    elif len(members) < 5:
        if full:
            return f"{aggregate([m.mention for m in members])} emotes usage in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"{aggregate([m.mention for m in members])} on {aggregate([c.mention for c in channels])} "
                f"emotes usage in {nmm:,} messages:"
            )
        else:
            return (
                f"{aggregate([m.mention for m in members])} on these {len(channels)} channels "
                f"emotes usage in {nmm:,} messages:"
            )
    else:
        if full:
            return f"These {len(members)} members emotes usage in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"These {len(members)} members on {aggregate([c.mention for c in channels])} "
                f"emotes usage in {nmm:,} messages:"
            )
        else:
            return (
                f"These {len(members)} members on these {len(channels)} channels "
                f"emotes usage in {nmm:,} messages:"
            )


def get_place(i: int) -> str:
    """
    Get the correct rank displayed (1st to 3rd have an emoji)
    """
    if i == 0:
        return ":first_place:"
    if i == 1:
        return ":second_place:"
    if i == 2:
        return ":third_place:"
    return f"**#{i + 1}**"


def get_usage(emote: Emote) -> str:
    """
    Get the correct usage displayed
    """
    if emote.usages == 0 and emote.reactions == 0:
        return "never used "
    elif emote.usages == 1:
        return "1 time "
    else:
        return f"{emote.usages:,} times "


def get_reactions(emote: Emote) -> str:
    """
    Get the correct reactions displayed
    """
    if emote.reactions == 0:
        return ""
    elif emote.reactions == 1:
        return "and 1 reaction "
    else:
        return f"and {emote.reactions:,} reactions "


def get_life(emote: Emote, show_life: bool) -> str:
    """
    Get the correct life span displayed
    """
    if not show_life or emote.default:
        return ""
    else:
        return f"(in {emote.life_days()} days) "


def get_last_used(emote: Emote) -> str:
    """
    Get the correct "last used" displayed
    """
    if emote.usages == 0 and emote.reactions == 0:
        return ""
    elif emote.use_days() == 0:
        return "(last used today)"
    elif emote.use_days() == 1:
        return "(last used yesterday)"
    else:
        return f"(last used {emote.use_days()} days ago)"


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
