from datetime import datetime
import discord
import re
import help
from utils import debug, aggregate, no_duplicate


# CLASSES

class Emote:
    def __init__(self, emoji):
        self.emoji = emoji
        self.name = str(emoji)
        self.usages = 0
        self.reactions = 0
        self.last_used = None

    def update_use(self, date):
        if self.last_used is None or date > self.last_used:
            self.last_used = date

    def used(self):
        return self.usages > 0 or self.reactions > 0

    def score(self):
        return self.usages + self.reactions + 1 / (100000 * (self.use_days() + 1))

    def life_days(self):
        return (datetime.today() - self.emoji.created_at).days

    def use_days(self):
        if self.last_used is None:
            return self.life_days()
        else:
            return (datetime.today() - self.last_used).days


# ANALYSIS


async def analyse_channel(channel, emotes, members, progress, delta, nc):
    nm = 0
    nmm = 0
    try:
        async for m in channel.history(limit=None):
            if not m.author.bot and (len(members) == 0 or m.author in members):
                found = [name for name in re.findall(r"(<:\w+:\d+>)", m.content) if name in emotes]
                for name in found:
                    emotes[name].usages += 1
                    emotes[name].update_use(m.created_at)
                nmm += 1
            if len(members) == 0:
                for reaction in m.reactions:
                    name = str(reaction.emoji)
                    if not (isinstance(reaction.emoji, str)) and name in emotes:
                        emotes[name].reactions += reaction.count
                        emotes[name].update_use(m.created_at)
            nm += 1
            if (delta + nm) % 1000 == 0:
                await progress.edit(content=f"```{(delta + nm) // 1000}k messages and {nc} channels analysed```")
        return nm, nmm
    except discord.errors.Forbidden:
        return -1, -1


# RESULTS


def get_message(emotes, full, channels, members, nmm, nc):
    if len(members) == 0:
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


def get_place(n):
    if n == 0:
        return ":first_place:"
    if n == 1:
        return ":second_place:"
    if n == 2:
        return ":third_place:"
    return f"**#{n + 1}**"


def get_usage(emote):
    if emote.usages == 0 and emote.reactions == 0:
        return "never used "
    elif emote.usages == 1:
        return "1 time "
    else:
        return f"{emote.usages} times "


def get_reactions(emote):
    if emote.reactions == 0:
        return ""
    elif emote.reactions == 1:
        return "and 1 reaction "
    else:
        return f"and {emote.reactions} reactions "


def get_life(emote, show_life):
    if not show_life:
        return ""
    else:
        return f"(in {emote.life_days()} days) "


def get_last_used(emote):
    if emote.usages == 0 and emote.reactions == 0:
        return ""
    elif emote.use_days() == 0:
        return "(last used today)"
    elif emote.use_days() == 1:
        return "(last used yesterday)"
    else:
        return f"(last used {emote.use_days()} days ago)"


def get_total(emotes, nmm):
    nu = 0
    nr = 0
    for name in emotes:
        nu += emotes[name].usages
        nr += emotes[name].reactions
    if nr > 0:
        return f"Total: {nu} times ({round(nu / nmm, 4)} / message) and {nr} reactions"
    else:
        return f"Total: {nu} times ({round(nu / nmm, 4)} / message)"


async def tell_results(first, emotes, channel, nmm, *, allow_unused, show_life):
    names = [name for name in emotes]
    names.sort(key=lambda name: emotes[name].score(), reverse=True)
    res = [first]
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


# MAIN


async def compute(message, args):
    debug(message, f"command '{message.content}'")

    guild = message.guild

    if len(args) > 1 and args[1] == "help":
        await help.compute(message, ["%help", "emotes"])
        return

    emotes = {str(emoji): Emote(emoji) for emoji in guild.emojis}

    channels = no_duplicate(message.channel_mentions)
    full = len(channels) == 0
    if full:
        channels = guild.text_channels

    members = no_duplicate(message.mentions)

    async with message.channel.typing():
        nm = 0
        nmm = 0
        nc = 0
        t0 = datetime.now()
        progress = await message.channel.send(f"```starting analysis...```")
        for channel in channels:
            nm1, nmm1 = await analyse_channel(channel, emotes, members, progress, nm, nc)
            if nm1 >= 0:
                nm += nm1
                nmm += nmm1
                nc += 1
        await progress.delete()
        await tell_results(get_message(emotes, full, channels, members, nmm, nc),
                           emotes, message.channel, nmm, allow_unused=full and len(members) == 0, show_life=False)
        dt = (datetime.now() - t0).total_seconds()
        debug(message, f"response sent {dt} s -> {nm / dt} m/s")
