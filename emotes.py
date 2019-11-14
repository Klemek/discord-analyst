from datetime import datetime
import discord
import re

# Custom libs
import help
from utils import debug, aggregate, no_duplicate

# CONSTANTS

CHUNK_SIZE = 10000


# MAIN

async def compute(message, args):
    """
    Computes the %emotes command

    :param message: message sent
    :type message: :class:`discord.Message`
    :param args: arguments of the command
    :type args: list[:class:`str`]
    """

    guild = message.guild

    # If "%emotes help" redirect to "%help emotes"
    if len(args) > 1 and args[1] == "help":
        await help.compute(message, ["%help", "emotes"])
        return

    # Create emotes dict from custom emojis of the guild
    emotes = {str(emoji): Emote(emoji) for emoji in guild.emojis}

    # Get selected channels or all of them if no channel arguments
    channels = no_duplicate(message.channel_mentions)
    full = len(channels) == 0
    if full:
        channels = guild.text_channels

    # Get selected members
    members = no_duplicate(message.mentions)

    # Start computing data
    async with message.channel.typing():
        nm = 0  # number of messages treated
        nmm = 0  # number of impacted messages
        nc = 0  # number of channel treated
        t0 = datetime.now()
        # Show custom progress message and keep it to update it later
        progress = await message.channel.send(f"```starting analysis...```")
        # Analyse every channel selected
        for channel in channels:
            nm1, nmm1 = await analyse_channel(channel, emotes, members, progress, nm, nc)
            # If treatment was successful, increase numbers
            if nm1 >= 0:
                nm += nm1
                nmm += nmm1
                nc += 1
        # Delete custom progress message
        await progress.delete()
        # Display results
        await tell_results(get_intro(emotes, full, channels, members, nmm, nc),
                           emotes, message.channel, nmm, allow_unused=full and len(members) == 0, show_life=False)
        dt = (datetime.now() - t0).total_seconds()
        debug(message, f"response sent {dt} s -> {nm / dt} m/s")


# CLASSES

class Emote:
    """
    Custom class to store emotes data

    :param emoji: source discord emoji
    :type emoji: :class:`discord.Emoji`
    :ivar emoji: discord emoji
    :vartype emoji: discord.Emoji
    :ivar usages: number of usages in messages
    :vartype usages: int
    :ivar reactions: number of reactions below messages (always 0 if member specified)
    :vartype reactions: int
    :ivar last_used: date of last use
    :vartype last_used: datetime
    """

    def __init__(self, emoji):
        self.emoji = emoji
        self.usages = 0
        self.reactions = 0
        self.last_used = None

    def update_use(self, date):
        """
        Update last use date if more recent

        :param date: date of use
        :type date: datetime
        """
        if self.last_used is None or date > self.last_used:
            self.last_used = date

    def used(self):
        """
        :return: If this emote was used ever
        :rtype: bool
        """
        return self.usages > 0 or self.reactions > 0

    def score(self):
        """
        :return: Score of this emote to be sorted
        :rtype: float
        """
        # Score is compose of usages + reactions
        # When 2 emotes have the same score, the days since last use is stored in the digits
        # (more recent first)
        return self.usages + self.reactions + 1 / (100000 * (self.use_days() + 1))

    def life_days(self):
        """
        :return: Days since creation
        :rtype: int
        """
        return (datetime.today() - self.emoji.created_at).days

    def use_days(self):
        """
        :return: Days since last use
        :rtype: int
        """
        # If never used, use creation date instead
        if self.last_used is None:
            return self.life_days()
        else:
            return (datetime.today() - self.last_used).days


# ANALYSIS

async def analyse_channel(channel, emotes, members, progress, nm0, nc):
    """
    Analyses a given channel

    :param channel: channel to analyse
    :type channel: discord.TextChannel
    :param emotes: known emotes
    :type emotes: dict[str, Emote]
    :param members: selected members or empty for all
    :type members: list[discord.Member]
    :param progress: custom progress message (already sent)
    :type progress: discord.Message
    :param nm0: number of already analysed messages
    :type nm0: int
    :param nc: number of already analysed channels
    :type nc: int
    :return: nm, nc (-1 on exception)
    :rtype: int, int
    """
    nm = 0
    nmm = 0
    try:
        messages = [None]
        while len(messages) >= CHUNK_SIZE or messages[-1] is None:
            messages = await channel.history(limit=CHUNK_SIZE, before=messages[-1]).flatten()
            for m in messages:
                tm0 = datetime.now()
                # If author is not bot or included in the selection (empty list is all)
                if not m.author.bot and (len(members) == 0 or m.author in members):
                    # Find all emotes un the current message in the form "<:emoji:123456789>"
                    # Filter for known emotes
                    found = [name for name in re.findall(r"(<:\w+:\d+>)", m.content) if name in emotes]
                    # For each emote, update its usage
                    for name in found:
                        emotes[name].usages += 1
                        emotes[name].update_use(m.created_at)
                    # Count this message as impacted
                    nmm += 1
                # For each reaction of this message, test if known emote and update when it's the case
                for reaction in m.reactions:
                    name = str(reaction.emoji)
                    # reaction.emoji can be only str, we don't want that
                    if not (isinstance(reaction.emoji, str)) and name in emotes:
                        if len(members) == 0:
                            emotes[name].reactions += reaction.count
                            emotes[name].update_use(m.created_at)
                        """ else:
                            users = await reaction.users().flatten()
                            for member in members:
                                if member in users:
                                    emotes[name].reactions += 1
                                    emotes[name].update_use(m.created_at)"""
            nm += len(messages)
            await progress.edit(content=f"```{nm0 + nm:,} messages and {nc} channels analysed```")
        return nm, nmm
    except discord.errors.HTTPException:
        # When an exception occurs (like Forbidden) sent -1
        return -1, -1


# RESULTS

async def tell_results(intro, emotes, channel, nmm, *, allow_unused, show_life):
    """
    Send the full results message

    :param intro: introduction sentence (from get_intro)
    :type intro: str
    :param emotes: known emotes
    :type emotes: dict[str, Emote]
    :param channel: where to send the message (original message channel)
    :type channel: discord.TextChannel
    :param nmm: number of impacted messages
    :type nmm: int
    :param allow_unused: show unused emotes
    :type allow_unused: bool
    :param show_life: show emotes life span
    :type show_life: bool
    """
    names = [name for name in emotes]
    names.sort(key=lambda name: emotes[name].score(), reverse=True)
    res = [intro]
    res += [
        f"{get_place(names.index(name))} {name} - "
        f"{get_usage(emotes[name])}"
        f"{get_reactions(emotes[name])}"
        f"{get_life(emotes[name], show_life)}"
        f"{get_last_used(emotes[name])}"
        for name in names if allow_unused or emotes[name].used()]
    res += [get_total(emotes, nmm)]
    response = ""
    for r in res:
        if len(response + "\n" + r) > 2000:
            await channel.send(response)
            response = ""
        response += "\n" + r
    if len(response) > 0:
        await channel.send(response)


def get_intro(emotes, full, channels, members, nmm, nc):
    """
    Get the introduction sentence of the response

    :param emotes: known emotes
    :type emotes: dict[str, Emote]
    :param full: if the scan contained all channels
    :type full: bool
    :param channels: channels selected (ignored if full is True)
    :type channels: list[discord.TextChannel]
    :param members: members selected (empty for all)
    :type members: list[discord.Member]
    :param nmm: number of messages impacted
    :type nmm: int
    :param nc: number of channels analysed
    :type nc: int
    :return: the correct intro sentence
    :rtype: str
    """
    # Show all data (members, channels) when it's less than 5 units
    if len(members) == 0:
        # Full scan of the server
        if full:
            return f"{len(emotes)} emotes in this server ({nc} channels, {nmm} messages):"
        elif len(channels) < 5:
            return f"{aggregate([c.mention for c in channels])} emotes usage in {nmm} messages:"
        else:
            return f"These {len(channels)} channels emotes usage in {nmm} messages:"
    elif len(members) < 5:
        if full:
            return f"{aggregate([m.mention for m in members])} emotes usage in {nmm} messages:"
        elif len(channels) < 5:
            return f"{aggregate([m.mention for m in members])} on {aggregate([c.mention for c in channels])} " \
                   f"emotes usage in {nmm} messages:"
        else:
            return f"{aggregate([m.mention for m in members])} on these {len(channels)} channels " \
                   f"emotes usage in {nmm} messages:"
    else:
        if full:
            return f"These {len(members)} members emotes usage in {nmm} messages:"
        elif len(channels) < 5:
            return f"These {len(members)} members on {aggregate([c.mention for c in channels])} " \
                   f"emotes usage in {nmm} messages:"
        else:
            return f"These {len(members)} members on these {len(channels)} channels " \
                   f"emotes usage in {nmm} messages:"


def get_place(i):
    """
    Get the correct rank displayed (1st to 3rd have an emoji)

    :param i: index
    :type i: int
    :return: rank string
    :rtype: str
    """
    if i == 0:
        return ":first_place:"
    if i == 1:
        return ":second_place:"
    if i == 2:
        return ":third_place:"
    return f"**#{i + 1}**"


def get_usage(emote):
    """
    Get the correct usage displayed

    :type emote: Emote
    :return: usage description
    :rtype: str
    """
    if emote.usages == 0 and emote.reactions == 0:
        return "never used "
    elif emote.usages == 1:
        return "1 time "
    else:
        return f"{emote.usages} times "


def get_reactions(emote):
    """
    Get the correct reactions displayed

    :return: reactions description
    :rtype: str
    """
    if emote.reactions == 0:
        return ""
    elif emote.reactions == 1:
        return "and 1 reaction "
    else:
        return f"and {emote.reactions} reactions "


def get_life(emote, show_life):
    """
    Get the correct life span displayed

    :type emote: Emote
    :param show_life: disable if False
    :type show_life: bool
    :return: life description
    :rtype: str
    """
    if not show_life:
        return ""
    else:
        return f"(in {emote.life_days()} days) "


def get_last_used(emote):
    """
    Get the correct "last used" displayed

    :type emote: Emote
    :return: last usage description
    :rtype: str
    """
    if emote.usages == 0 and emote.reactions == 0:
        return ""
    elif emote.use_days() == 0:
        return "(last used today)"
    elif emote.use_days() == 1:
        return "(last used yesterday)"
    else:
        return f"(last used {emote.use_days()} days ago)"


def get_total(emotes, nmm):
    """
    Get the total of all emotes used

    :param emotes: known emotes
    :type emotes: dict[str, Emote]
    :param nmm: number of messages impacted
    :type nmm: int
    :return: total sentence
    :rtype: str
    """
    nu = 0
    nr = 0
    for name in emotes:
        nu += emotes[name].usages
        nr += emotes[name].reactions
    if nr > 0:
        return f"Total: {nu} times ({round(nu / nmm, 4)} / message) and {nr} reactions"
    else:
        return f"Total: {nu} times ({round(nu / nmm, 4)} / message)"
